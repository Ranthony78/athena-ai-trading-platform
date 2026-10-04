"""
Assembles the intraday Analysis Report payload: current stats,
support/resistance, multi-timeframe trend, ATM option data, and the last
AI Analysis run for this symbol. The 60-session daily chart was removed
because this workspace is designed for day traders.

This is symbol-only, timeframe-agnostic by design (matches the "fixed
block" report format, not the interval-picker AI Analysis flow) — it
always uses daily candles for the chart/range and a fixed multi-
timeframe set for trend context.

Every section degrades gracefully to null/empty if its data isn't
available (no user, no NFO import, provider error) — same "real data
or NA" principle as everywhere else, never fabricates a chart point
or a stat.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

MULTI_TIMEFRAME_SET = ["5m", "15m", "30m"]


class AnalysisReportService:

    @classmethod
    def get_report(cls, symbol: str, user=None) -> dict:
        report = {
            "symbol": symbol,
            "session": cls._safe(cls._get_session),
            "spot": cls._safe(cls._get_spot, symbol, user),
            "price_history": [],
            "range_high": None,
            "range_low": None,
            "range_label": None,
            "support_resistance": cls._safe(cls._get_support_resistance, symbol),
            "multi_timeframe": cls._safe(cls._get_multi_timeframe, symbol) or {},
            "options": cls._safe(cls._get_options, symbol, user),
            "key_metrics": cls._safe(cls._get_key_metrics, symbol, user),
            "core_calculations": cls._safe(cls._get_core_calculations, symbol, user),
            "gap_analysis": cls._safe(cls._get_gap_analysis, symbol, user),
            "time_blocks": cls._safe(cls._get_time_blocks, symbol),
            "last_analysis": cls._safe(cls._get_last_analysis, symbol),
        }

        return report

    # ------------------------------------------------------------------
    # Helper: run a section, log+null it on any failure rather than
    # letting one bad section break the whole report.
    # ------------------------------------------------------------------

    @staticmethod
    def _safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"AnalysisReportService section error [{fn.__name__}]: {e}")
            return None

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    @staticmethod
    def _get_session() -> dict:
        from ..engine.market_state import MarketState

        return MarketState.session_info()

    @staticmethod
    def _get_spot(symbol: str, user) -> dict:
        from .market_service import MarketService

        return MarketService(user=user).quote(symbol)

    @staticmethod
    def _get_time_blocks(symbol: str) -> Optional[dict]:
        from .time_block_service import TimeBlockService

        return TimeBlockService.build(symbol)

    @staticmethod
    def _get_gap_analysis(symbol: str, user) -> Optional[dict]:
        """
        Today's opening gap, how much of it price has given back, and how
        sessions with the same gap category closed relative to their open.
        Continuation = closed further in the gap's direction. These are
        historical frequencies, not a forecast.
        """
        from django.utils import timezone

        from .historical_distribution_service import HistoricalDistributionService
        from .market_read_service import MarketReadService
        from .market_service import MarketService
        from .session_metrics_service import SessionMetrics

        if not user:
            return None
        quote = MarketService(user=user).quote(symbol) or {}
        gap = SessionMetrics.gap_retrace(
            quote.get("close"), quote.get("open"), quote.get("ltp")
        )
        if not gap:
            return None
        result = {"gap": gap, "historical": {"available": False, "reason": None}}
        if gap["direction"] == "FLAT":
            result["historical"][
                "reason"
            ] = "The open was flat, so there is no gap to study."
            return result

        bucket = MarketReadService._gap_bucket(quote)
        stats = HistoricalDistributionService.close_direction_given_gap(
            symbol, bucket, exclude_date=timezone.localdate()
        )
        if not stats or stats.get("error"):
            result["historical"]["reason"] = (
                "Fewer than 10 historical sessions had this gap category, "
                "so no base rate is shown."
            )
            return result

        same, opposite = (
            ("up_pct", "down_pct")
            if gap["direction"] == "UP"
            else ("down_pct", "up_pct")
        )
        result["historical"] = {
            "available": True,
            "gap_bucket": bucket,
            "continuation_pct": stats[same],
            "reversal_pct": stats[opposite],
            "flat_pct": stats["flat_pct"],
            "sample_size": stats["sample_size"],
            "low_confidence": stats.get("low_confidence", False),
        }
        return result

    @staticmethod
    def _get_core_calculations(symbol: str, user) -> Optional[dict]:
        from .core_calculations_service import CoreCalculationsService

        return CoreCalculationsService.build(symbol, user)

    @staticmethod
    def _get_key_metrics(symbol: str, user) -> dict:
        """
        Facts for the workspace price strip: front-month futures VWAP,
        volume and OI, India VIX with its change, the opening-gap retrace
        and index breadth. Each part is None when it cannot be verified.
        """
        from .futures_service import FuturesService
        from .market_breadth_service import MarketBreadthService
        from .market_service import MarketService
        from .session_metrics_service import SessionMetrics

        def part(fn, *args):
            try:
                return fn(*args)
            except Exception as e:
                logger.error(
                    f"AnalysisReportService key metric [{getattr(fn, "__name__", "part")}]: {e}"
                )
                return None

        def vix_part():
            quote = MarketService(user=user).quote("VIX") if user else None
            if not quote or not quote.get("ltp"):
                return None
            return {
                "ltp": quote.get("ltp"),
                "change_pct": SessionMetrics.pct_change(
                    quote.get("close"), quote.get("ltp")
                ),
                "high": quote.get("high") or None,
            }

        def gap_part():
            quote = MarketService(user=user).quote(symbol) if user else None
            quote = quote or {}
            return SessionMetrics.gap_retrace(
                quote.get("close"), quote.get("open"), quote.get("ltp")
            )

        return {
            "futures": part(FuturesService.snapshot, symbol, user),
            "vix": part(vix_part),
            "gap": part(gap_part),
            "breadth": part(MarketBreadthService.get_breadth, user, symbol),
        }

    @staticmethod
    def _get_support_resistance(symbol: str) -> dict:
        from .daily_levels_service import DailyLevelsService

        # Pivots/CPR come from the previous completed daily session, not
        # from the previous 15-minute candle.
        data = DailyLevelsService.levels(symbol)
        if not data:
            return {"cpr": {}, "pivot": {}, "based_on": None}

        def rounded(values):
            return {k: round(v, 2) for k, v in values.items()}

        return {
            "cpr": rounded(data["cpr"]),
            "pivot": rounded(data["pivot"]),
            "based_on": data["based_on"],
        }

    @staticmethod
    def _get_multi_timeframe(symbol: str) -> dict:
        from ..indicators.indicator_service import IndicatorService
        from ..repositories.candle_repository import CandleRepository
        from ..repositories.instrument_repository import InstrumentRepository

        instrument = InstrumentRepository.get_by_symbol(symbol)
        results = {}

        for tf in MULTI_TIMEFRAME_SET:
            try:
                data = IndicatorService.calculate(
                    symbol=symbol,
                    timeframe=tf,
                    indicators=["EMA_20", "EMA_50", "RSI_14"],
                    limit=120,
                )
                ema_vals = [v for v in (data.get("EMA_20") or []) if v is not None]
                ema50_vals = [v for v in (data.get("EMA_50") or []) if v is not None]
                rsi_vals = [v for v in (data.get("RSI_14") or []) if v is not None]

                if not ema_vals or not rsi_vals or not instrument:
                    results[tf] = None
                    continue

                candles = list(
                    CandleRepository.get_by_instrument_and_timeframe(
                        instrument=instrument,
                        timeframe=tf,
                        limit=1,
                    ).values("close")
                )
                latest_close = float(candles[0]["close"]) if candles else None
                latest_ema = round(ema_vals[-1], 2)

                if latest_close is None:
                    trend = "NA"
                elif latest_close > latest_ema:
                    trend = "Bullish"
                elif latest_close < latest_ema:
                    trend = "Bearish"
                else:
                    trend = "Neutral"

                results[tf] = {
                    "trend": trend,
                    "ema_20": latest_ema,
                    # EMAs are seeded from the first candle, so with fewer than
                    # 50 candles the value is not a real 50-period EMA.
                    "ema_50": (
                        round(ema50_vals[-1], 2) if len(ema50_vals) >= 50 else None
                    ),
                    "rsi_14": round(rsi_vals[-1], 2),
                }
            except Exception as e:
                logger.error(f"AnalysisReportService multi-timeframe error [{tf}]: {e}")
                results[tf] = None

        return results

    @staticmethod
    def _get_options(symbol: str, user) -> dict:
        if not user:
            return None
        from .option_chain_service import OptionChainService

        service = OptionChainService(user=user)
        summary = service.get_chain_summary(symbol)
        if not summary.get("atm_strike"):
            return None

        chain = service.get_chain(symbol, expiry=summary.get("expiry"))
        atm_call = next(
            (
                r
                for r in chain
                if r.get("strike") == summary["atm_strike"]
                and r.get("option_type") == "CE"
            ),
            None,
        )
        atm_put = next(
            (
                r
                for r in chain
                if r.get("strike") == summary["atm_strike"]
                and r.get("option_type") == "PE"
            ),
            None,
        )

        from datetime import date

        from django.utils import timezone

        from .strike_selection_service import StrikeSelectionService

        try:
            dte = (
                date.fromisoformat(str(summary.get("expiry"))) - timezone.localdate()
            ).days
        except (TypeError, ValueError):
            dte = None

        matched_put = (
            StrikeSelectionService.premium_matched_put(chain, atm_call.get("ltp"))
            if atm_call
            else None
        )

        return {
            "expiry": summary.get("expiry"),
            "dte": dte,
            "lot_size": (atm_call or atm_put or {}).get("lot_size"),
            "atm_strike": summary.get("atm_strike"),
            "pcr_oi": summary.get("pcr_oi"),
            "pcr_volume": summary.get("pcr_volume"),
            "max_pain": summary.get("max_pain"),
            "atm_call": atm_call,
            "atm_put": atm_put,
            # Put whose premium best matches the ATM call (None if no close match).
            "matched_put": matched_put,
            "oi_walls": StrikeSelectionService.oi_walls(
                chain, summary.get("spot_price")
            ),
        }

    @staticmethod
    def _get_last_analysis(symbol: str) -> dict:
        from django.utils import timezone

        from apps.ai_engine.repositories.ai_repository import AnalysisSessionRepository

        from ..repositories.instrument_repository import InstrumentRepository

        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return None

        sessions = AnalysisSessionRepository.get_by_instrument(instrument, limit=5)
        latest = next((s for s in sessions if s.status == "COMPLETE"), None)
        if not latest:
            return None

        minutes_ago = round((timezone.now() - latest.session_time).total_seconds() / 60)
        parsed = latest.parsed_output or {}

        return {
            "session_id": latest.id,
            "run_at": latest.session_time.isoformat(),
            "minutes_ago": minutes_ago,
            "signal": parsed.get("signal"),
            "confidence": parsed.get("confidence"),
        }
