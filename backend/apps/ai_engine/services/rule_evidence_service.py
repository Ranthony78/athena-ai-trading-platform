"""Deterministic, read-only context checks inspired by Athena's rule notes.

These measurements are descriptive evidence for the AI analyst. They are
not a strategy score, probability, recommendation, or order instruction.
"""

import logging
import math
from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


class RuleEvidenceService:
    VERSION = "athena-evidence-v3"
    PREMIUM_MARGIN = 1.15
    MOMENTUM_MIN = 0.25
    MOMENTUM_MAX = 0.65
    OI_IMPACT_CLAMP = 0.50
    VOLATILITY_RATIO_SCALE = 50.0
    REGULAR_SESSION_MINUTES = 375

    @classmethod
    def parameters(cls):
        """Expose all nine reference values and make inactive weights explicit."""
        return [
            {
                "key": "profit_margin",
                "label": "Profit margin",
                "value": cls.PREMIUM_MARGIN,
                "unit": "× ATM premium",
                "status": "active_reference",
                "applied": True,
            },
            {
                "key": "momentum_min",
                "label": "Momentum band minimum",
                "value": cls.MOMENTUM_MIN,
                "unit": "× daily 1σ move",
                "status": "active_reference",
                "applied": True,
            },
            {
                "key": "momentum_max",
                "label": "Momentum band maximum",
                "value": cls.MOMENTUM_MAX,
                "unit": "× daily 1σ move",
                "status": "active_reference",
                "applied": True,
            },
            {
                "key": "oi_clamp",
                "label": "OI build-up / unwind clamp",
                "value": cls.OI_IMPACT_CLAMP,
                "unit": "maximum absolute impact",
                "status": "inactive_data_unavailable",
                "applied": False,
                "reason": "No comparable historical OI snapshots are stored.",
            },
            {
                "key": "volatility_ratio_scale",
                "label": "Volatility ratio scale",
                "value": cls.VOLATILITY_RATIO_SCALE,
                "unit": "points per 1.0 ratio",
                "status": "active_display_scale",
                "applied": True,
            },
            {
                "key": "orb_bonus",
                "label": "ORB breakout bonus",
                "value": 15.0,
                "unit": "proposed points",
                "status": "inactive_uncalibrated",
                "applied": False,
                "reason": "Raw opening-range evidence is shown; bonus scoring is disabled until outcome validation.",
            },
            {
                "key": "momentum_bonus",
                "label": "Momentum bonus maximum",
                "value": 20.0,
                "unit": "proposed points",
                "status": "inactive_uncalibrated",
                "applied": False,
                "reason": "Raw momentum evidence is shown; bonus scoring is disabled until outcome validation.",
            },
            {
                "key": "oi_bonus",
                "label": "OI build-up / unwind bonus maximum",
                "value": 15.0,
                "unit": "proposed points",
                "status": "inactive_data_unavailable",
                "applied": False,
                "reason": "Requires comparable historical OI snapshots and outcome validation.",
            },
            {
                "key": "cpr_bonus",
                "label": "CPR narrowness bonus maximum",
                "value": 15.0,
                "unit": "proposed points",
                "status": "inactive_uncalibrated",
                "applied": False,
                "reason": "Raw CPR-width evidence is shown; bonus scoring is disabled until outcome validation.",
            },
        ]

    @classmethod
    def build(
        cls,
        *,
        symbol,
        instrument,
        quote,
        vix,
        options,
        historical,
        session,
        horizon_minutes,
        market_provider,
    ):
        """Build a source-labelled packet from already fetched data and stored candles."""
        as_of = timezone.now()
        verified_provider = str(market_provider or "").lower() == "zerodha"
        spot = cls._number((quote or {}).get("ltp")) if verified_provider else None
        vix_pct = cls._number((vix or {}).get("ltp")) if verified_provider else None
        horizon = max(1, int(horizon_minutes or 15))

        expected = None
        if spot and spot > 0 and vix_pct and vix_pct > 0:
            # India VIX is annualized. This is a square-root-of-time 1σ
            # approximation over regular NSE trading minutes, not a forecast.
            expected = (
                spot
                * (vix_pct / 100)
                * math.sqrt(horizon / (252 * cls.REGULAR_SESSION_MINUTES))
            )
        expected_points = round(expected, 2) if expected is not None else None
        daily_sigma = None
        if spot and spot > 0 and vix_pct and vix_pct > 0:
            daily_sigma = spot * (vix_pct / 100) / math.sqrt(252)
        daily_candles = (
            cls._verified_daily_candles(instrument, session)
            if verified_provider
            else []
        )

        option_data = (options or {}) if verified_provider else {}
        call = option_data.get("atm_call") or {}
        put = option_data.get("atm_put") or {}
        premium_hurdle = {
            "margin_multiple": cls.PREMIUM_MARGIN,
            "expected_move_points": expected_points,
            "call": cls._premium_side(call, expected, cls.PREMIUM_MARGIN),
            "put": cls._premium_side(put, expected, cls.PREMIUM_MARGIN),
            "source": "ATM option-chain LTP and India VIX quote, fetched for this analysis",
            "note": "A price-move/premium comparison only; excludes fees, spread, theta, IV changes and execution. It is not a profitability estimate or entry rule.",
        }

        vol_context = cls._volatility_context(daily_sigma, daily_candles)

        momentum = cls._momentum(
            quote if verified_provider else None, daily_sigma, session
        )
        orb = cls._opening_range_evidence(instrument, spot, session)
        cpr = cls._cpr_evidence(daily_candles)

        return {
            "version": cls.VERSION,
            "as_of": as_of.isoformat(),
            "read_only": True,
            "parameters": cls.parameters(),
            "disclaimer": "Deterministic market context for AI interpretation only; no aggregate score, probability adjustment, or order action.",
            "expected_move": {
                "horizon_minutes": horizon,
                "one_sigma_points": expected_points,
                "basis": "India VIX annualized volatility, square-root-of-time scaled by 252 trading days × 375 regular-session minutes",
                "source": "India VIX quote and index quote fetched for this analysis",
                "status": "available" if expected_points is not None else "unavailable",
                "reason": (
                    None
                    if expected_points is not None
                    else (
                        "Requires Zerodha verified market data, positive index LTP, and India VIX quote."
                    )
                ),
            },
            "premium_hurdle": premium_hurdle,
            "daily_move_comparison": cls._daily_move_comparison(
                daily_sigma, daily_candles
            ),
            "option_buying_audit": cls._option_buying_audit(
                option_data, expected_points, horizon
            ),
            "momentum_band": momentum,
            "oi_evidence": {
                "status": "unavailable",
                "current_pcr_oi": (
                    option_data.get("pcr_oi") if verified_provider else None
                ),
                "reserved_clamp_pct": round(cls.OI_IMPACT_CLAMP * 100),
                "clamp_applied": False,
                "source": "Current option-chain snapshot only",
                "reason": "Athena does not retain comparable prior option-chain OI snapshots, so fresh OI build-up/unwind cannot be verified. Current OI/PCR alone is not treated as OI change; the reserved ±50% impact clamp is not applied until verified OI deltas exist.",
            },
            "volatility_context": vol_context
            or {
                "status": "unavailable",
                "source": "India VIX quote and stored daily candles",
                "reason": "Requires a valid India VIX quote and a nonzero historical median full-session range.",
            },
            "opening_range": (
                orb
                if verified_provider
                else {
                    "status": "unavailable",
                    "source": "Stored Zerodha 5-minute candles",
                    "reason": "Unavailable while the configured market provider is not Zerodha.",
                }
            ),
            "cpr_context": cpr,
        }

    @staticmethod
    def _number(value):
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _verified_daily_candles(instrument, session):
        if not instrument:
            return []
        try:
            from apps.market_data.models import Candle

            today = datetime.now(IST).date()
            if session and session.get("date"):
                today = datetime.fromisoformat(session["date"]).date()
            completed_filter = (
                {"candle_time__date__lte": today}
                if (session or {}).get("session") == "CLOSED"
                else {"candle_time__date__lt": today}
            )
            return list(
                Candle.objects.filter(
                    instrument=instrument,
                    timeframe="1d",
                    source="ZERODHA",
                    **completed_filter,
                )
                .order_by("-candle_time")
                .values("candle_time", "open", "high", "low", "close")[:1260]
            )
        except Exception as exc:
            logger.warning("Could not load verified daily candles: %s", exc)
            return []

    @classmethod
    def _option_buying_audit(cls, options, expected_points, horizon):
        """Expose p9 research requirements without manufacturing a trading edge."""
        options = options or {}
        legs = [options.get("atm_call") or {}, options.get("atm_put") or {}]
        mids = []
        asks = []
        for leg in legs:
            bid, ask = cls._number(leg.get("best_bid")), cls._number(
                leg.get("best_ask")
            )
            if bid is None or ask is None or bid <= 0 or ask < bid:
                mids = asks = []
                break
            mids.append((bid + ask) / 2)
            asks.append(ask)
        return {
            "version": "option-buying-input-audit-v1",
            "horizon_minutes": horizon,
            "straddle_mid_points": round(sum(mids), 2) if len(mids) == 2 else None,
            "straddle_ask_debit_points": (
                round(sum(asks), 2) if len(asks) == 2 else None
            ),
            "vix_horizon_one_sigma_points": expected_points,
            "edge_scores": None,
            "option_win_probability": None,
            "net_expectancy": None,
            "filters": [
                {
                    "key": "A",
                    "label": "IV velocity versus decay",
                    "status": "INVALID_UNITS",
                    "reason": "IV percentage points per minute cannot be compared directly with theta currency per 15 minutes. Requires IV history and a vega-based premium impact model with consistent time units.",
                },
                {
                    "key": "B",
                    "label": "Straddle movement hurdle",
                    "status": "REFERENCE_ONLY" if mids else "UNAVAILABLE",
                    "reason": "Combined premium is an expiry breakeven reference before costs, not a verified intraday required move. A one-sigma estimate does not establish positive expectancy.",
                },
                {
                    "key": "C",
                    "label": "ATM OI change and volume impulse",
                    "status": "UNAVAILABLE",
                    "reason": "Comparable timestamped 15–30 minute OI and volume snapshots and a validated threshold are not stored. Static PCR is not OI change.",
                },
                {
                    "key": "D",
                    "label": "Gamma amplification",
                    "status": "UNAVAILABLE",
                    "reason": "Current model-estimated gamma may be supplied, but a five-day gamma median and verified dealer-position evidence are unavailable.",
                },
                {
                    "key": "E",
                    "label": "Spread tightening and volume spike",
                    "status": "UNAVAILABLE",
                    "reason": "A current bid/ask snapshot cannot establish tightening versus the opening spread or a volume spike; comparable historical snapshots are required.",
                },
            ],
            "note": "Research input audit only. Unknown is not false or a passing filter. No 4-of-5 score, win probability, regime probability, IV-crush probability or expectancy is inferred. Existing mode, freshness, time cutoff and paper eligibility gates remain authoritative.",
        }

    @classmethod
    def _daily_move_comparison(cls, daily_sigma, daily_candles):
        """Compare like-duration daily moves without altering horizon forecasts."""
        moves = []
        # Rows arrive newest first. Invalid sessions do not become zero moves.
        for row in daily_candles[:15]:
            opening = cls._number(row.get("open"))
            closing = cls._number(row.get("close"))
            if (
                opening is not None
                and closing is not None
                and opening > 0
                and closing > 0
            ):
                moves.append(abs(closing - opening))
        valid_sigma = cls._number(daily_sigma)
        available = len(moves) == 15 and valid_sigma is not None and valid_sigma > 0
        historical = sum(moves) / len(moves) if moves else None
        return {
            "status": "available" if available else "unavailable",
            "sample_size": len(moves),
            "required_sessions": 15,
            "vix_daily_one_sigma_points": (
                round(valid_sigma, 2)
                if valid_sigma is not None and valid_sigma > 0
                else None
            ),
            "historical_mean_absolute_open_close_points": (
                round(historical, 2) if historical is not None else None
            ),
            "experimental_daily_blend_points": (
                round((valid_sigma + historical) / 2, 2) if available else None
            ),
            "source": "India VIX daily estimate and latest 15 completed daily Zerodha candles",
            "reason": (
                None
                if available
                else "Requires positive VIX daily estimate and 15 valid completed sessions with open and close prices."
            ),
            "note": "Equal-weight daily blend inspired by algo_ai; descriptive and uncalibrated. Mean absolute open-to-close movement is not standard deviation. Do not rescale this blend to an intraday horizon or use it as profit probability, premium eligibility, or an entry rule.",
        }

    @classmethod
    def _volatility_context(cls, daily_sigma, daily_candles):
        unavailable = {
            "status": "unavailable",
            "source": "India VIX quote and completed daily Zerodha candles",
            "reason": "Requires a valid India VIX quote and at least 30 verified completed daily ranges.",
        }
        if daily_sigma is None:
            return unavailable
        ranges = [
            float(row["high"]) - float(row["low"])
            for row in daily_candles
            if row["high"] is not None
            and row["low"] is not None
            and float(row["high"]) > float(row["low"])
        ]
        if len(ranges) < 30:
            return unavailable
        ranges.sort()
        middle = len(ranges) // 2
        median_range = (
            ranges[middle]
            if len(ranges) % 2
            else (ranges[middle - 1] + ranges[middle]) / 2
        )
        if median_range <= 0:
            return unavailable
        ratio = daily_sigma / median_range
        return {
            "daily_one_sigma_points": round(daily_sigma, 2),
            "historical_median_full_session_range_points": round(median_range, 2),
            "ratio": round(ratio, 3),
            "scaled_context_pct": min(100, round(ratio * cls.VOLATILITY_RATIO_SCALE)),
            "scale": cls.VOLATILITY_RATIO_SCALE,
            "sample_size": len(ranges),
            "source": "India VIX quote compared with completed daily Zerodha candle ranges",
            "note": "Relative volatility context, not forecast confidence or direction. The 0–100 display is a capped ratio scale, not calibrated probability.",
        }

    @classmethod
    def _premium_side(cls, option, expected, margin):
        premium = cls._number(option.get("ltp"))
        if premium is None or premium <= 0 or expected is None:
            return {
                "premium": premium,
                "threshold_points": None,
                "move_to_threshold_ratio": None,
                "status": "unavailable",
            }
        threshold = premium * margin
        return {
            "premium": round(premium, 2),
            "threshold_points": round(threshold, 2),
            "move_to_threshold_ratio": (
                round(expected / threshold, 3) if threshold else None
            ),
            "status": (
                "estimate_above_reference"
                if expected >= threshold
                else "estimate_below_reference"
            ),
        }

    @classmethod
    def _momentum(cls, quote, daily_sigma, session):
        quote = quote or {}
        session = session or {}
        open_price = cls._number(quote.get("open"))
        ltp = cls._number(quote.get("ltp"))
        if not session.get("is_live"):
            return {
                "status": "unavailable",
                "reason": "Momentum-band comparison is only shown during the clock-reported live session; closed-market quotes may be stale.",
                "source": "Index quote and market-session clock",
            }
        if not open_price or ltp is None or daily_sigma is None or daily_sigma <= 0:
            return {
                "status": "unavailable",
                "reason": "Requires current-session open, LTP, and India VIX-derived daily 1σ move.",
                "source": "Index quote and India VIX quote",
            }
        move = ltp - open_price
        fraction = abs(move) / daily_sigma
        status = (
            "below_reference_band"
            if fraction < RuleEvidenceService.MOMENTUM_MIN
            else (
                "within_reference_band"
                if fraction <= RuleEvidenceService.MOMENTUM_MAX
                else "beyond_reference_band"
            )
        )
        return {
            "status": status,
            "direction": "up" if move > 0 else "down" if move < 0 else "flat",
            "move_from_open_points": round(move, 2),
            "fraction_of_daily_one_sigma": round(fraction, 3),
            "reference_min": RuleEvidenceService.MOMENTUM_MIN,
            "reference_max": RuleEvidenceService.MOMENTUM_MAX,
            "source": "Index quote and India VIX quote fetched during clock-reported live session",
            "note": "Reference band only; an in-band value is not a signal or entry condition.",
        }

    @classmethod
    def _opening_range_evidence(cls, instrument, spot, session):
        unavailable = {
            "status": "unavailable",
            "source": "Stored 5-minute candles marked Zerodha",
            "reason": "No verified opening-range candle set is available for this session.",
        }
        try:
            if not instrument:
                return unavailable
            from apps.market_data.models import Candle

            now = datetime.now(IST)
            session_date = now.date()
            if session and session.get("date"):
                session_date = datetime.fromisoformat(session["date"]).date()
            rows = list(
                Candle.objects.filter(
                    instrument=instrument,
                    timeframe="5m",
                    source="ZERODHA",
                    candle_time__date=session_date,
                )
                .order_by("candle_time")
                .values("candle_time", "high", "low")[:10]
            )
            opening_rows = [
                row
                for row in rows
                if time(9, 15)
                <= timezone.localtime(row["candle_time"], IST).time()
                < time(9, 30)
            ]
            opening_rows = opening_rows[:3]
            if len(opening_rows) != 3 or spot is None:
                return {
                    **unavailable,
                    "reason": "Needs all three verified 5-minute candles from 09:15–09:30 IST and a current index quote.",
                }
            high = max(float(row["high"]) for row in opening_rows)
            low = min(float(row["low"]) for row in opening_rows)
            status = (
                "above_opening_range"
                if spot > high
                else "below_opening_range" if spot < low else "inside_opening_range"
            )
            return {
                "status": status,
                "high": round(high, 2),
                "low": round(low, 2),
                "comparison_price": round(spot, 2),
                "opening_candles": 3,
                "source": "Three stored Zerodha 5-minute candles (09:15–09:30 IST) and index quote",
                "note": "Descriptive range position only; no breakout order or signal is generated.",
            }
        except Exception as exc:
            logger.warning("Could not build opening-range evidence: %s", exc)
            return unavailable

    @classmethod
    def _cpr_evidence(cls, daily_candles):
        unavailable = {
            "status": "unavailable",
            "source": "Stored daily Zerodha candles",
            "reason": "Insufficient verified completed daily candles to compare CPR width.",
        }
        try:
            usable = [
                row
                for row in daily_candles[:61]
                if float(row["high"]) > float(row["low"])
            ]
            if len(usable) < 11:
                return {
                    **unavailable,
                    "reason": "Needs at least 11 verified completed daily candles; fewer are available.",
                }

            ratios = []
            for row in usable:
                high, low, close = (
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                )
                pp = (high + low + close) / 3
                bc = (high + low) / 2
                tc = 2 * pp - bc
                ratios.append(abs(tc - bc) / (high - low))
            current_ratio = ratios[0]
            baseline = sorted(ratios[1:])
            median = baseline[len(baseline) // 2]
            return {
                "status": (
                    "narrower_than_recent_median"
                    if current_ratio <= median
                    else "wider_than_recent_median"
                ),
                "cpr_width_points": round(
                    current_ratio
                    * (float(usable[0]["high"]) - float(usable[0]["low"])),
                    2,
                ),
                "width_as_pct_of_prior_day_range": round(current_ratio * 100, 2),
                "recent_median_width_pct": round(median * 100, 2),
                "sample_size": len(baseline),
                "reference_date": timezone.localtime(usable[0]["candle_time"], IST)
                .date()
                .isoformat(),
                "source": "CPR derived from prior completed Zerodha daily OHLC; compared with preceding daily-candle ratios",
                "note": "Relative-width context only; narrower CPR has no guaranteed directional outcome.",
            }
        except Exception as exc:
            logger.warning("Could not build CPR evidence: %s", exc)
            return unavailable
