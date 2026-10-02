"""Read-only, source-labelled snapshot for the Options Workspace."""

import logging
import math
from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

logger = logging.getLogger(__name__)


class MarketReadService:
    """Compose existing quote, history, and indicator data without mutations."""

    @classmethod
    def get_snapshot(cls, symbol: str, user=None) -> dict:
        from ..indicators.indicator_service import IndicatorService
        from ..engine.market_state import MarketState
        from ..repositories.candle_repository import CandleRepository
        from ..repositories.instrument_repository import InstrumentRepository
        from .historical_distribution_service import HistoricalDistributionService
        from .market_service import MarketService

        symbol = symbol.upper()
        session_date = MarketState.now_ist().date()
        session = cls._safe_session()
        cls._refresh_live_candles_if_needed(symbol, user, session, session_date)
        market = MarketService(user=user)
        quote = cls._safe("quote", market.quote, symbol)
        history = cls._safe(
            "intraday range history",
            HistoricalDistributionService.intraday_range_stats,
            symbol,
            exclude_date=session_date,
        )

        probability = None
        gap_bucket = cls._gap_bucket(quote)
        if gap_bucket:
            probability = cls._safe(
                "conditional close distribution",
                HistoricalDistributionService.close_direction_given_gap,
                symbol,
                gap_bucket,
                exclude_date=session_date,
            )

        indicators = cls._safe(
            "indicators",
            IndicatorService.calculate,
            symbol=symbol,
            timeframe="15m",
            indicators=["PIVOT", "CPR", "EMA_20", "RSI_14"],
            limit=100,
        ) or {}

        instrument = InstrumentRepository.get_by_symbol(symbol)
        latest_candle = (
            CandleRepository.get_latest(instrument, "15m")
            if instrument else None
        )
        last_candle_time = (
            latest_candle.candle_time.isoformat()
            if latest_candle and latest_candle.candle_time else None
        )
        last_daily_candle_time = cls._previous_daily_candle_time(
            instrument, CandleRepository, session_date,
        )
        age_minutes = cls._age_minutes(latest_candle.candle_time) if latest_candle else None
        freshness_limit = 30 if (session or {}).get("session") == "LIVE" else 72 * 60
        intraday_is_stale = age_minutes is None or age_minutes > freshness_limit
        session_vwap, vwap_candle_count, session_candle_count = cls._session_vwap(
            instrument, CandleRepository,
        )

        spot = cls._number((quote or {}).get("ltp"))
        today_open = cls._number((quote or {}).get("open"))
        previous_close = cls._number((quote or {}).get("close"))
        range_stats = history if isinstance(history, dict) and not history.get("error") else None
        range_points = (range_stats or {}).get("upside_from_open_points", {})
        down_points = (range_stats or {}).get("downside_from_open_points", {})
        median_up = cls._number(range_points.get("median"))
        median_down = cls._number(down_points.get("median"))

        range_guide = None
        if today_open and median_up is not None and median_down is not None:
            range_guide = {
                "low": round(max(0, today_open - median_down), 2),
                "high": round(today_open + median_up, 2),
                "open": today_open,
                "median_up_points": median_up,
                "median_down_points": median_down,
                "sample_size": range_stats.get("sample_size"),
                "low_confidence": range_stats.get("low_confidence", False),
                "historical_through": last_daily_candle_time,
            }
        range_unavailable_reason = None
        if not range_guide:
            if history and history.get("error"):
                range_unavailable_reason = (
                    f"Only {history.get('sample_size', 0)} valid daily sessions are stored; "
                    "at least 30 are required for this historical reference."
                )
            elif not today_open:
                range_unavailable_reason = "The configured market-data provider did not return a valid session open."
            else:
                range_unavailable_reason = "Stored daily candles do not contain enough valid sessions to calculate the historical range reference."

        pivot = cls._latest_values((indicators or {}).get("PIVOT")) if not intraday_is_stale else {}
        cpr = cls._latest_values((indicators or {}).get("CPR")) if not intraday_is_stale else {}
        levels = cls._levels(pivot, cpr, spot) if not intraday_is_stale else {
            "support": None,
            "resistance": None,
            "cpr": {},
            "pivot": {},
            "available": False,
            "unavailable_reason": "Withheld because the latest stored 15-minute candle is stale.",
        }
        if not levels.get("available") and not levels.get("unavailable_reason"):
            levels["unavailable_reason"] = "Stored 15-minute candles did not produce usable pivot or CPR values."

        if intraday_is_stale:
            vwap_unavailable_reason = "Withheld because the latest stored 15-minute candle is stale."
            ema_unavailable_reason = vwap_unavailable_reason
            rsi_unavailable_reason = vwap_unavailable_reason
        else:
            vwap_unavailable_reason = (
                "No current-session 15-minute candles are stored."
                if not session_candle_count
                else f"Stored {symbol} index candles have no positive volume, so a volume-weighted price cannot be calculated."
                if not vwap_candle_count
                else None
            )
            ema_unavailable_reason = (
                "Not enough valid 15-minute closing prices are available to calculate EMA 20."
                if cls._last_value((indicators or {}).get("EMA_20")) is None else None
            )
            rsi_unavailable_reason = (
                "Not enough valid 15-minute price changes are available to calculate RSI 14."
                if cls._last_value((indicators or {}).get("RSI_14")) is None else None
            )

        return {
            "symbol": symbol,
            "as_of": timezone.now().isoformat(),
            "session": session,
            "quote": {
                "spot": spot,
                "today_open": today_open,
                "previous_close": previous_close,
                "gap_pct": cls._gap_percent(today_open, previous_close),
                "gap_bucket": gap_bucket,
                "timestamp": (quote or {}).get("timestamp"),
            },
            "probability": cls._probability(probability, gap_bucket, last_daily_candle_time),
            "range_guide": range_guide,
            "range_history": {
                "sample_size": (range_stats or history or {}).get("sample_size"),
                "median_points": cls._number((range_stats or {}).get("range_points", {}).get("median")),
                "p95_points": cls._number((range_stats or {}).get("range_points", {}).get("p95")),
                "available": range_stats is not None,
                "unavailable_reason": range_unavailable_reason,
            },
            "levels": levels,
            "indicators": {
                "vwap": session_vwap if not intraday_is_stale else None,
                "vwap_candle_count": vwap_candle_count if not intraday_is_stale else 0,
                "vwap_session_candle_count": session_candle_count if not intraday_is_stale else 0,
                "vwap_unavailable_reason": vwap_unavailable_reason,
                "ema_20": cls._last_value((indicators or {}).get("EMA_20")) if not intraday_is_stale else None,
                "ema_20_unavailable_reason": ema_unavailable_reason,
                "rsi_14": cls._last_value((indicators or {}).get("RSI_14")) if not intraday_is_stale else None,
                "rsi_14_unavailable_reason": rsi_unavailable_reason,
            },
            "freshness": {
                "intraday_is_stale": intraday_is_stale,
                "intraday_age_minutes": age_minutes,
                "intraday_limit_minutes": freshness_limit,
                "daily_history_last_candle_at": last_daily_candle_time,
            },
            "source": {
                "quote": "Configured market-data provider",
                "quote_fetched_at": timezone.now().isoformat(),
                "indicators": "Stored 15-minute candles; stale technical values are withheld",
                "last_candle_at": last_candle_time,
                "last_daily_candle_at": last_daily_candle_time,
                "daily_history": "Stored daily candles",
            },
        }

    @staticmethod
    def _safe(label, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            logger.exception("MarketReadService %s unavailable", label)
            return None

    @staticmethod
    def _number(value):
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _age_minutes(candle_time):
        if not candle_time:
            return None
        try:
            latest = timezone.localtime(candle_time, ZoneInfo("Asia/Kolkata"))
            now = timezone.localtime(timezone.now(), ZoneInfo("Asia/Kolkata"))
            return max(0, round((now - latest).total_seconds() / 60))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _gap_percent(cls, today_open, previous_close):
        open_value = cls._number(today_open)
        close_value = cls._number(previous_close)
        if not open_value or not close_value:
            return None
        return round((open_value - close_value) / close_value * 100, 2)

    @classmethod
    def _gap_bucket(cls, quote):
        if not quote:
            return None
        gap_pct = cls._gap_percent(quote.get("open"), quote.get("close"))
        if gap_pct is None or gap_pct == 0:
            return None
        magnitude = abs(gap_pct)
        size = "normal" if magnitude <= 0.3 else "mild" if magnitude <= 0.8 else "large" if magnitude <= 1.5 else "extreme"
        return f"gap_{'up' if gap_pct > 0 else 'down'}_{size}"

    @classmethod
    def _probability(cls, result, gap_bucket, historical_through=None):
        if not result or result.get("error"):
            sample_size = (result or {}).get("sample_size")
            reason = (
                f"Only {sample_size} historical sessions matched this opening-gap category; "
                "at least 10 are required to show a base rate."
                if sample_size is not None
                else "No reliable historical sample is available for this opening-gap category."
            )
            return {
                "available": False,
                "reason": reason,
                "gap_bucket": gap_bucket,
                "sample_size": sample_size,
            }
        return {
            "available": True,
            "horizon": "Full-session close relative to that session's open",
            "gap_bucket": result.get("gap_bucket"),
            "up_pct": result.get("up_pct"),
            "down_pct": result.get("down_pct"),
            "flat_pct": result.get("flat_pct"),
            "flat_threshold_pct": result.get("flat_threshold_pct"),
            "sample_size": result.get("sample_size"),
            "low_confidence": result.get("low_confidence", False),
            "historical_through": historical_through,
            "basis": "Observed outcomes among historical sessions with the same opening-gap category; descriptive base rate, not a forecast.",
        }

    @classmethod
    def _latest_values(cls, series):
        if not isinstance(series, dict):
            return {}
        return {key: cls._last_value(values) for key, values in series.items()}

    @classmethod
    def _session_vwap(cls, instrument, repository):
        if not instrument:
            return None, 0, 0
        from ..engine.market_state import MarketState

        now = MarketState.now_ist()
        start = datetime.combine(now.date(), time(9, 15), tzinfo=ZoneInfo("Asia/Kolkata"))
        candles = repository.get_range(
            instrument=instrument,
            timeframe="15m",
            from_time=start,
            to_time=now,
        ).values("high", "low", "close", "volume")
        session_candle_count = len(candles)
        weighted_total = 0.0
        volume_total = 0.0
        count = 0
        for candle in candles:
            volume = cls._number(candle.get("volume"))
            high = cls._number(candle.get("high"))
            low = cls._number(candle.get("low"))
            close = cls._number(candle.get("close"))
            if volume is None or volume <= 0 or high is None or low is None or close is None:
                continue
            weighted_total += ((high + low + close) / 3) * volume
            volume_total += volume
            count += 1
        return (round(weighted_total / volume_total, 2) if volume_total else None), count, session_candle_count

    @staticmethod
    def _previous_daily_candle_time(instrument, repository, session_date):
        if not instrument:
            return None
        rows = repository.get_by_instrument_and_timeframe(
            instrument=instrument,
            timeframe="1d",
            limit=5,
        ).values_list("candle_time", flat=True)
        for candle_time in rows:
            local_time = timezone.localtime(candle_time, ZoneInfo("Asia/Kolkata"))
            if local_time.date() < session_date:
                return local_time.isoformat()
        return None

    @classmethod
    def _last_value(cls, series):
        if isinstance(series, (list, tuple)):
            for value in reversed(series):
                number = cls._number(value)
                if number is not None:
                    return number
            return None
        return cls._number(series)

    @classmethod
    def _levels(cls, pivot, cpr, spot):
        candidates = []
        for source, values, keys in (
            ("Pivot", pivot, ("s1", "s2", "s3", "pp", "r1", "r2", "r3")),
            ("CPR", cpr, ("bc", "pp", "tc")),
        ):
            for key in keys:
                value = cls._number(values.get(key))
                if value is not None:
                    candidates.append({"name": key.upper(), "value": round(value, 2), "method": source})

        supports = [level for level in candidates if spot is not None and level["value"] < spot]
        resistances = [level for level in candidates if spot is not None and level["value"] > spot]
        return {
            "support": max(supports, key=lambda level: level["value"]) if supports else None,
            "resistance": min(resistances, key=lambda level: level["value"]) if resistances else None,
            "cpr": cpr,
            "pivot": pivot,
            "available": bool(candidates),
            "unavailable_reason": None if candidates else "Stored 15-minute candles did not produce usable pivot or CPR values.",
        }

    @staticmethod
    def _safe_session():
        try:
            from ..engine.market_state import MarketState
            return MarketState.session_info()
        except Exception:
            return None

    @classmethod
    def _refresh_live_candles_if_needed(cls, symbol, user, session, session_date):
        """Refresh the stored 15-minute source used by Market Read during live hours."""
        if (session or {}).get("session") != "LIVE":
            return

        try:
            from django.conf import settings
            from django.core.cache import cache
            from ..engine.market_state import MarketState
            from ..repositories.candle_repository import CandleRepository
            from ..repositories.instrument_repository import InstrumentRepository
            from .candle_service import CandleService

            if getattr(settings, "MARKET_PROVIDER", "mock") != "zerodha":
                return

            instrument = InstrumentRepository.get_by_symbol(symbol)
            if not instrument:
                return

            now = MarketState.now_ist()
            expected_minute = now.minute - (now.minute % 15)
            expected_bucket = now.replace(minute=expected_minute, second=0, microsecond=0)
            latest = CandleRepository.get_latest(instrument, "15m")
            if latest and latest.candle_time:
                latest_local = timezone.localtime(latest.candle_time, ZoneInfo("Asia/Kolkata"))
                if latest_local.date() == session_date and latest_local >= expected_bucket:
                    return

            # The Market Read endpoint polls frequently. Limit provider
            # backfills to once a minute per symbol and market session.
            refresh_key = f"market-read-candle-refresh:{symbol}:{session_date.isoformat()}"
            if not cache.add(refresh_key, True, timeout=60):
                return

            CandleService(user=user).fetch_and_store(
                symbol=symbol,
                timeframe="15m",
                from_date=str(session_date),
                to_date=str(session_date),
            )
        except Exception as error:
            logger.warning("Live 15-minute candle refresh failed for %s: %s", symbol, error)
