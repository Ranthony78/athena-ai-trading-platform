"""Experimental, deterministic eligibility gate for a long ATM straddle.

This gate creates a paper-test candidate only. It does not change Athena's
AI signal, historical probabilities, or authorize a live order.
"""
from datetime import timedelta
import math

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class VolatilitySetupService:
    VERSION = "paper-long-straddle-v1"
    PREMIUM_BUFFER = 1.15
    ELEVATED_VOLATILITY_RATIO = 1.0
    MAX_QUOTE_AGE_SECONDS = 120
    MAX_SPREAD_PCT = 10.0
    SLIPPAGE_BPS_PER_LEG = 10
    BROKERAGE_PER_ORDER = 20.0

    @classmethod
    def build_candidate(cls, *, parsed, context, user):
        """Return a user-visible candidate and internal leg identifiers."""
        context = context or {}
        evidence = context.get("rule_evidence") or {}
        expected = evidence.get("expected_move") or {}
        reasons = []
        try:
            expected_horizon = int(expected.get("horizon_minutes"))
            request_horizon = int(context.get("forecast_horizon_minutes"))
        except (TypeError, ValueError):
            expected_horizon = request_horizon = None
        if expected_horizon is None or request_horizon is None or expected_horizon != request_horizon:
            reasons.append("The VIX move estimate must match the selected forecast horizon.")
        volatility = evidence.get("volatility_context") or {}
        options = context.get("options") or {}
        call = options.get("atm_call") or {}
        put = options.get("atm_put") or {}
        now = timezone.now()

        if context.get("analysis_mode") != "LIVE":
            reasons.append("A next-session outlook cannot create a current-session setup.")
        if not (context.get("session") or {}).get("is_live"):
            reasons.append("A live market session is required.")
        if str(getattr(settings, "MARKET_PROVIDER", "mock")).lower() != "zerodha" or context.get("quote_source") != "ZERODHA":
            reasons.append("Verified Zerodha market data is required; mock data is excluded.")

        # Reuse the simulator's conservative timestamp parser and freshness window.
        from apps.paper_trading.services.broker_simulator import BrokerSimulator
        underlying_quote = context.get("quote") or {}
        if BrokerSimulator._quote_is_stale(underlying_quote.get("timestamp")):
            reasons.append("The underlying quote is stale or undated.")
        vix_quote = context.get("vix") or {}
        if BrokerSimulator._quote_is_stale(vix_quote.get("timestamp")):
            reasons.append("The India VIX quote used for the move estimate is stale or undated.")

        try:
            ratio = float(volatility.get("ratio"))
        except (TypeError, ValueError):
            ratio = None
        if ratio is not None and not math.isfinite(ratio):
            ratio = None
        if volatility.get("status") == "unavailable" or ratio is None:
            reasons.append("Relative volatility needs India VIX and at least 30 verified completed daily ranges.")
        elif ratio < cls.ELEVATED_VOLATILITY_RATIO:
            reasons.append("Relative volatility is below the experimental elevated-volatility threshold.")

        try:
            expected_points = float(expected.get("one_sigma_points"))
            call_premium = float(call.get("ltp"))
            put_premium = float(put.get("ltp"))
            call_ask = float(call.get("best_ask"))
            put_ask = float(put.get("best_ask"))
        except (TypeError, ValueError):
            expected_points = call_premium = put_premium = call_ask = put_ask = None
        if expected_points is None or not math.isfinite(expected_points) or expected_points <= 0:
            reasons.append("A positive VIX-scaled move estimate for this forecast horizon is required.")
            expected_points = None
        if any(value is None or not math.isfinite(value) or value <= 0 for value in (call_premium, put_premium)):
            reasons.append("Fresh, positive premiums for both ATM legs are required.")
            if call_premium is None or not math.isfinite(call_premium) or call_premium <= 0:
                call_premium = None
            if put_premium is None or not math.isfinite(put_premium) or put_premium <= 0:
                put_premium = None
        if any(value is None or not math.isfinite(value) or value <= 0 for value in (call_ask, put_ask)):
            reasons.append("A valid ask-side buy price for each option leg is required for the combined-debit test.")
            if call_ask is None or not math.isfinite(call_ask) or call_ask <= 0:
                call_ask = None
            if put_ask is None or not math.isfinite(put_ask) or put_ask <= 0:
                put_ask = None

        call_age = cls._quote_age(call.get("quote_timestamp"), now)
        put_age = cls._quote_age(put.get("quote_timestamp"), now)
        if call_age is None or put_age is None or max(call_age, put_age) > cls.MAX_QUOTE_AGE_SECONDS:
            reasons.append("Both option quotes must have verified timestamps no more than two minutes old.")

        call_spread = cls._spread_pct(call)
        put_spread = cls._spread_pct(put)
        if call_spread is None or put_spread is None:
            reasons.append("Both option legs need valid best bid and ask prices to check liquidity.")
        elif max(call_spread, put_spread) > cls.MAX_SPREAD_PCT:
            reasons.append(f"An option bid/ask spread exceeds the experimental {cls.MAX_SPREAD_PCT:g}% limit.")

        expiry = options.get("expiry")
        strike = options.get("atm_strike")
        if not expiry or not strike or not call or not put:
            reasons.append("A matched ATM CE/PE pair and expiry are required.")
        if call.get("strike") != strike or put.get("strike") != strike or call.get("expiry") != expiry or put.get("expiry") != expiry:
            reasons.append("The call and put must share the same ATM strike and expiry.")

        # This is an explicit high-risk flag only; an unavailable event calendar
        # stays unknown and is disclosed rather than treated as researched.
        risks = parsed.get("risks") or []
        if any(any(term in str(risk).lower() for term in ("high event risk", "major scheduled event", "high-impact event")) for risk in risks):
            reasons.append("A supplied risk flag identifies high event risk.")

        lot_size = call.get("lot_size")
        if not lot_size or lot_size != put.get("lot_size"):
            reasons.append("Both option legs must have the same verified lot size.")

        combined_premium = call_ask + put_ask if call_ask and put_ask else None
        slippage_points = combined_premium * cls.SLIPPAGE_BPS_PER_LEG / 10000 if combined_premium else None
        cost_points = (cls.BROKERAGE_PER_ORDER / float(lot_size) + slippage_points) if lot_size and slippage_points is not None else None
        hurdle_points = combined_premium * cls.PREMIUM_BUFFER + cost_points if combined_premium and cost_points is not None else None
        if expected_points is not None and hurdle_points is not None and expected_points < hurdle_points:
            reasons.append("The horizon-matched move estimate does not clear the combined-premium hurdle plus estimated paper costs.")

        legs = []
        if not reasons and user:
            from apps.market_data.models import Instrument
            for option, option_type in ((call, "CE"), (put, "PE")):
                instrument = Instrument.objects.filter(
                    trading_symbol=option.get("trading_symbol"), exchange="NFO",
                    symbol=options.get("symbol") or context.get("symbol") or "NIFTY",
                    option_type=option_type, strike=strike, expiry=expiry,
                    lot_size=lot_size, is_active=True,
                ).first()
                if not instrument:
                    reasons.append(f"No active listed NFO {option_type} contract matches the verified quote.")
                    break
                legs.append({
                    "instrument_id": instrument.id,
                    "option_type": option_type,
                    "trading_symbol": instrument.trading_symbol,
                    "strike": float(instrument.strike),
                    "expiry": instrument.expiry.isoformat(),
                    "entry_premium": round(float(option["ltp"]), 2),
                    "estimated_buy_price": round(float(option["best_ask"]), 2),
                    "lot_size": instrument.lot_size,
                    "quote_timestamp": str(option.get("quote_timestamp")),
                    "spread_pct": round(cls._spread_pct(option), 2),
                })
        elif not user:
            reasons.append("An authenticated user is required to resolve listed contracts.")

        eligible = not reasons and len(legs) == 2
        return {
            "version": cls.VERSION,
            "eligible": eligible,
            "status": "ELIGIBLE" if eligible else "NOT_ELIGIBLE",
            "paper_only": True,
            "experimental": True,
            "horizon_minutes": expected.get("horizon_minutes"),
            "expected_move_points": round(expected_points, 2) if expected_points is not None else None,
            "volatility_ratio": round(ratio, 3) if ratio is not None else None,
            "volatility_ratio_threshold": cls.ELEVATED_VOLATILITY_RATIO,
            "combined_premium_per_unit": round(combined_premium, 2) if combined_premium is not None else None,
            "estimated_cost_per_unit": round(cost_points, 4) if cost_points is not None else None,
            "required_move_points": round(hurdle_points, 2) if hurdle_points is not None else None,
            "maximum_loss_per_lot_before_taxes": round(combined_premium * float(lot_size), 2) if combined_premium is not None and lot_size else None,
            "quote_max_age_seconds": max(call_age, put_age) if call_age is not None and put_age is not None else None,
            "event_calendar_status": ((context.get("market_drivers") or {}).get("event_calendar") or {}).get("status", "unknown"),
            "legs": legs if eligible else [],
            "reasons": reasons,
            "method_note": "Experimental paper-test gate: relative daily volatility ratio ≥1.0 and horizon-matched VIX 1σ move ≥1.15× the combined ATM ask-side debit plus estimated brokerage/slippage. Paper fills also use ask for buys and bid for sells. This is not a calibrated profit probability or guarantee; taxes, IV change and theta are not fully modeled.",
        }

    @staticmethod
    def _quote_age(value, now):
        stamp = parse_datetime(str(value)) if value else None
        if stamp is None:
            return None
        if timezone.is_naive(stamp):
            stamp = timezone.make_aware(stamp)
        age = (now - stamp).total_seconds()
        return max(0, age) if age >= -60 else None

    @classmethod
    def _spread_pct(cls, option):
        try:
            bid, ask = float(option.get("best_bid")), float(option.get("best_ask"))
            if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid:
                return None
            midpoint = (ask + bid) / 2
            return ((ask - bid) / midpoint) * 100 if midpoint else None
        except (TypeError, ValueError):
            return None
