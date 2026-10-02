"""Sourced macro coverage. Headlines are context, never a live price feed."""
from datetime import timedelta
from urllib.parse import urlparse

from django.utils import timezone
from django.utils.dateparse import parse_datetime


class MarketDriversService:
    TOPICS = (
        ("global", "Global markets", ("nasdaq", "dow", "s&p", "asian", "nikkei", "hang seng", "gift nifty", "wall street")),
        ("crude", "Crude oil", ("crude", "brent", "wti", "oil price", "opec")),
        ("currency", "USD / INR", ("rupee", "usd/inr", "usd-inr", "dollar")),
        ("events", "Scheduled events and policy", ("rbi", "fed", "fomc", "budget", "earnings", "election", "inflation", "repo rate")),
        ("india", "Indian market and sectors", ("nifty", "sensex", "india", "sector", "bank", "nse")),
    )

    @classmethod
    def build(cls, news, user=None):
        now = timezone.now()
        rows = []
        for key, label, keywords in cls.TOPICS:
            articles = []
            for item in (news or {}).get("headlines", []):
                title = str(item.get("title") or "")
                if not any(word in title.lower() for word in keywords):
                    continue
                try:
                    published = parse_datetime(str(item.get("published_at") or ""))
                    if published and timezone.is_naive(published):
                        published = timezone.make_aware(published)
                except (TypeError, ValueError):
                    published = None
                url = str(item.get("url") or "")
                source = item.get("source")
                fresh = bool(published and now - timedelta(hours=24) <= published <= now + timedelta(minutes=1))
                linked = urlparse(url).scheme in ("http", "https") and bool(urlparse(url).netloc)
                articles.append({
                    "title": title[:500], "source": source,
                    "url": url if linked else None,
                    "published_at": published.isoformat() if published else None,
                    "usable": bool(fresh and linked and source),
                    "status": "current" if fresh and linked and source else "stale_or_unverified",
                })
            usable = [item for item in articles if item["usable"]]
            rows.append({
                "key": key, "label": label,
                "status": "available" if usable else "unavailable",
                "articles": articles[:5],
                "reason": None if usable else "No linked, dated article from the last 24 hours is available for this topic.",
                "limitation": "News coverage only. Live prices and a verified event calendar are not supplied by this feed.",
            })
        return {"version": "market-drivers-v2", "as_of": now.isoformat(), "topics": rows,
                "market_quotes": [
                    cls._front_month_quote("Crude oil futures", ("CRUDEOIL", "CRUDEOILM"), "MCX", user, now),
                    cls._front_month_quote("USD/INR futures", ("USDINR",), "CDS", user, now),
                ],
                "global_market_prices": {"status": "unavailable", "source": None,
                    "reason": "No verified global-index quote source is configured. Global-market headlines are shown separately."},
                "event_calendar": {"status": "unavailable", "source": None,
                    "reason": "No verified scheduled-event calendar is connected. Policy/news headlines are not treated as a calendar."},
                "source": "Marketaux financial news" if news else "Not available",
                "note": "Coverage can be incomplete. Publication time differs from event time; do not infer an event schedule from a headline."}

    @staticmethod
    def _front_month_quote(label, symbols, exchange, user, now):
        unavailable = {
            "label": label, "status": "unavailable", "ltp": None, "source": None,
            "quote_time": None, "expiry": None,
            "reason": f"No active, unexpired {exchange} futures contract is present in Athena's instrument catalog.",
        }
        if not user:
            return {**unavailable, "reason": "An authenticated Zerodha session is required for this quote."}
        try:
            from django.conf import settings
            from apps.market_data.models import Instrument
            from apps.market_data.services.market_service import MarketService

            if getattr(settings, "MARKET_PROVIDER", "mock") != "zerodha":
                return {**unavailable, "reason": "A verified Zerodha market-data provider is not configured; mock data is excluded."}

            contract = Instrument.objects.filter(
                symbol__in=symbols,
                exchange=exchange,
                instrument_type="FUT",
                expiry__gte=timezone.localdate(),
                is_active=True,
            ).order_by("expiry").first()
            if not contract:
                return unavailable

            service = MarketService(user=user)
            if getattr(service.provider, "data_source", "UNKNOWN") != "ZERODHA":
                return {**unavailable, "reason": "The selected quote adapter is not a verified Zerodha source."}
            quote = service.quote(contract.trading_symbol)
            try:
                ltp = float(quote.get("ltp")) if quote and quote.get("ltp") is not None else None
            except (TypeError, ValueError):
                ltp = None
            if ltp is None or ltp <= 0:
                return {**unavailable, "expiry": contract.expiry.isoformat() if contract.expiry else None,
                        "contract": contract.trading_symbol,
                        "reason": "The front-month contract exists, but Zerodha returned no last traded price."}

            timestamp = quote.get("timestamp") or quote.get("quote_timestamp") or quote.get("last_trade_time")
            parsed = parse_datetime(str(timestamp)) if timestamp else None
            if parsed and timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed)
            if parsed and parsed.year < 2000:
                parsed = None
            age_seconds = (now - parsed).total_seconds() if parsed else None
            fresh = age_seconds is not None and 0 <= age_seconds <= 300
            return {
                "label": label,
                "status": "fresh" if fresh else "stale_or_unverified",
                "ltp": ltp if fresh else None,
                "last_ltp": ltp,
                "source": "Zerodha Kite",
                "exchange": exchange,
                "contract": contract.trading_symbol,
                "expiry": contract.expiry.isoformat() if contract.expiry else None,
                "quote_time": parsed.isoformat() if parsed else None,
                "age_seconds": round(age_seconds) if age_seconds is not None else None,
                "reason": None if fresh else (
                    "Zerodha returned no valid trade timestamp; excluded from current evidence."
                    if parsed is None else
                    "Last price is older than five minutes; excluded from current evidence."
                ),
            }
        except Exception as exc:
            # Avoid logging provider exception text: requests URLs can contain auth data.
            return {**unavailable, "reason": f"Quote source unavailable ({type(exc).__name__})."}
