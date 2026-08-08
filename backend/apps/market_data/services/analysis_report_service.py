"""
Assembles the full Analysis Report payload: real price history + EMA
overlay, current stats, support/resistance, multi-timeframe trend,
ATM option data, and the last AI Analysis run for this symbol.

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
from datetime import date, timedelta

logger = logging.getLogger(__name__)

CHART_SESSIONS = 60  # trading sessions of real daily history to fetch
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
            "last_analysis": cls._safe(cls._get_last_analysis, symbol),
        }

        history = cls._safe(cls._get_price_history, symbol, user)
        if history:
            report["price_history"] = history["candles"]
            report["range_high"] = history["range_high"]
            report["range_low"] = history["range_low"]
            report["range_label"] = f"{history['session_count']}-Session"

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
    def _get_price_history(symbol: str, user) -> dict:
        """
        Fetch real daily candles live (not assumed pre-stored), persist
        them for reuse, then compute EMA20/EMA50 for the chart overlay.
        """
        from .candle_service import CandleService
        from ..indicators.indicator_service import IndicatorService

        service = CandleService(user=user)

        to_date = date.today()
        from_date = to_date - timedelta(days=int(CHART_SESSIONS * 1.6))  # buffer for weekends/holidays

        count = service.fetch_and_store(
            symbol=symbol,
            timeframe="1d",
            from_date=str(from_date),
            to_date=str(to_date),
        )
        if not count:
            return None

        candles = list(
            service.get_candles(symbol=symbol, timeframe="1d", limit=CHART_SESSIONS)
            .values("candle_time", "close")
        )
        candles.reverse()  # ascending chronological order for a chart

        if not candles:
            return None

        indicators = IndicatorService.calculate(
            symbol=symbol, timeframe="1d",
            indicators=["EMA_20", "EMA_50"], limit=CHART_SESSIONS,
        )
        ema20_series = indicators.get("EMA_20") or []
        ema50_series = indicators.get("EMA_50") or []

        rows = []
        for i, c in enumerate(candles):
            rows.append({
                "date": str(c["candle_time"])[:10],
                "close": float(c["close"]),
                "ema_20": round(ema20_series[i], 2) if i < len(ema20_series) and ema20_series[i] is not None else None,
                "ema_50": round(ema50_series[i], 2) if i < len(ema50_series) and ema50_series[i] is not None else None,
            })

        closes = [r["close"] for r in rows]
        return {
            "candles": rows,
            "range_high": max(closes),
            "range_low": min(closes),
            "session_count": len(rows),
        }

    @staticmethod
    def _get_support_resistance(symbol: str) -> dict:
        from ..indicators.indicator_service import IndicatorService

        data = IndicatorService.calculate(
            symbol=symbol, timeframe="15m", indicators=["CPR", "PIVOT"], limit=50,
        )

        def latest(series):
            if isinstance(series, list):
                vals = [v for v in series if v is not None]
                return round(vals[-1], 2) if vals else None
            return series

        cpr = data.get("CPR") or {}
        pivot = data.get("PIVOT") or {}
        return {
            "cpr": {k: latest(v) for k, v in cpr.items()},
            "pivot": {k: latest(v) for k, v in pivot.items()},
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
                    symbol=symbol, timeframe=tf,
                    indicators=["EMA_20", "RSI_14"], limit=60,
                )
                ema_vals = [v for v in (data.get("EMA_20") or []) if v is not None]
                rsi_vals = [v for v in (data.get("RSI_14") or []) if v is not None]

                if not ema_vals or not rsi_vals or not instrument:
                    results[tf] = None
                    continue

                candles = list(
                    CandleRepository.get_by_instrument_and_timeframe(
                        instrument=instrument, timeframe=tf, limit=1,
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
            (r for r in chain if r.get("strike") == summary["atm_strike"] and r.get("option_type") == "CE"),
            None,
        )
        atm_put = next(
            (r for r in chain if r.get("strike") == summary["atm_strike"] and r.get("option_type") == "PE"),
            None,
        )

        return {
            "expiry": summary.get("expiry"),
            "atm_strike": summary.get("atm_strike"),
            "pcr_oi": summary.get("pcr_oi"),
            "pcr_volume": summary.get("pcr_volume"),
            "max_pain": summary.get("max_pain"),
            "atm_call": atm_call,
            "atm_put": atm_put,
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