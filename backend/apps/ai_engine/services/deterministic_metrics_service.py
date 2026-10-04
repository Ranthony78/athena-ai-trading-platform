"""
Computed, read-only market facts handed to the model as context.

Everything here is calculated from stored or live data by plain code; the
model only narrates it. Each section is None (never a guess) when its
inputs are missing, so the prompt shows "NA" for it.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Intraday bars used for the up/down-bar volume check.
VOLUME_CHECK_BARS = 20


class DeterministicMetricsService:

    @classmethod
    def build(
        cls,
        symbol: str,
        user,
        quote: Optional[dict],
        vix: Optional[dict],
        candles: list[dict],
        options: Optional[dict] = None,
        horizon_minutes: Optional[int] = None,
        analysis_mode: str = "LIVE",
    ) -> dict:
        from apps.market_data.services.analysis_report_service import (
            AnalysisReportService,
        )
        from apps.market_data.services.core_calculations_service import (
            CoreCalculationsService,
        )
        from apps.market_data.services.daily_levels_service import DailyLevelsService
        from apps.market_data.services.futures_service import FuturesService
        from apps.market_data.services.profit_probability_service import (
            ProfitProbabilityService,
        )
        from apps.market_data.services.session_metrics_service import SessionMetrics
        from apps.market_data.services.snapshot_signals_service import (
            SnapshotSignalsService,
        )
        from apps.market_data.services.time_block_service import TimeBlockService

        quote = quote or {}
        vix = vix or {}

        def safe(label, fn, *args):
            try:
                return fn(*args)
            except Exception as e:
                logger.error(f"DeterministicMetrics {label} error: {e}")
                return None

        spot = quote.get("ltp")
        core = safe(
            "core calculations",
            CoreCalculationsService.from_context,
            symbol,
            options,
            cls._number(vix.get("ltp")),
        )
        return {
            "daily_levels": safe("daily levels", DailyLevelsService.levels, symbol),
            "gap_retrace": safe(
                "gap retrace",
                SessionMetrics.gap_retrace,
                quote.get("close"),
                quote.get("open"),
                spot,
            ),
            "vix_change_pct": safe(
                "vix change",
                SessionMetrics.pct_change,
                vix.get("close"),
                vix.get("ltp"),
            ),
            "vix_intraday_high": vix.get("high") or None,
            "volume_confirmation": safe(
                "volume confirmation",
                SessionMetrics.volume_confirmation,
                candles[-VOLUME_CHECK_BARS:],
            ),
            "futures": safe("futures", FuturesService.snapshot, symbol, user),
            "oi_walls": (options or {}).get("oi_walls"),
            "core_calculations": core,
            "profit_probability": (
                safe(
                    "profit probability",
                    ProfitProbabilityService.from_core,
                    symbol,
                    core,
                    horizon_minutes,
                    analysis_mode,
                )
                if core and horizon_minutes
                else None
            ),
            "gap_history": safe(
                "gap history", AnalysisReportService._get_gap_analysis, symbol, user
            ),
            "time_blocks": safe("time blocks", TimeBlockService.build, symbol),
            "snapshot_signals": safe(
                "snapshot signals", SnapshotSignalsService.compute, symbol
            ),
        }

    @staticmethod
    def _number(value) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def as_prompt_text(metrics: Optional[dict]) -> str:
        """Compact text block; every missing value prints as NA."""
        metrics = metrics or {}

        def val(value):
            return "NA" if value in (None, "", {}) else value

        gap = metrics.get("gap_retrace") or {}
        vol = metrics.get("volume_confirmation") or {}
        fut = metrics.get("futures") or {}
        walls = metrics.get("oi_walls") or {}
        call_wall = walls.get("call_wall") or {}
        put_wall = walls.get("put_wall") or {}
        based_on = (metrics.get("daily_levels") or {}).get("based_on") or {}
        core = metrics.get("core_calculations") or {}
        move = core.get("required_move") or {}
        greeks = core.get("straddle_greeks") or {}
        velocity = core.get("iv_velocity") or {}
        history = (metrics.get("gap_history") or {}).get("historical") or {}
        signals = metrics.get("snapshot_signals") or {}
        oi_ce = (signals.get("oi_change") or {}).get("CE") or {}
        oi_pe = (signals.get("oi_change") or {}).get("PE") or {}
        spike_ce = (signals.get("volume_spike") or {}).get("CE") or {}
        spike_pe = (signals.get("volume_spike") or {}).get("PE") or {}
        profit = metrics.get("profit_probability") or {}
        structures = profit.get("structures") or {}

        def freq(name):
            return val((structures.get(name) or {}).get("historical_pct"))

        blocks = (metrics.get("time_blocks") or {}).get("blocks") or []
        block_text = "; ".join(
            f"{b['window']}: {val(b.get('bias'))}, volatility {val(b.get('volatility'))}, "
            f"trend {val(b.get('trend_strength'))} ({b.get('sessions')} sessions)"
            for b in blocks
        )
        return "\n".join(
            [
                f"- Pivot/CPR based on session: {val(based_on.get('date'))}",
                f"- Gap: {val(gap.get('direction'))} {val(gap.get('gap_points'))} pts; "
                f"retraced {val(gap.get('retrace_pct'))}%",
                f"- India VIX change vs previous close: {val(metrics.get('vix_change_pct'))}% "
                f"(intraday high {val(metrics.get('vix_intraday_high'))})",
                f"- Up/down-bar volume (last bars): {val(vol.get('verdict'))}, "
                f"up share {val(vol.get('up_share_pct'))}%",
                f"- Front-month futures {val(fut.get('contract'))}: LTP {val(fut.get('ltp'))}, "
                f"VWAP {val(fut.get('vwap'))}, volume {val(fut.get('volume'))}, OI {val(fut.get('oi'))}",
                f"- Option OI walls: call {val(call_wall.get('strike'))} "
                f"(OI {val(call_wall.get('oi'))}), put {val(put_wall.get('strike'))} "
                f"(OI {val(put_wall.get('oi'))})",
                f"- Black-76 (parity forward {val(core.get('forward'))}): implied volatility "
                f"{val(core.get('implied_vol'))}%, synthetic straddle {val(core.get('straddle'))}, "
                f"IV velocity {val(velocity.get('change_per_window'))} pts per "
                f"{val(velocity.get('window_minutes'))} min",
                f"- Required move to recover premium: call {val(move.get('call'))}, "
                f"put {val(move.get('put'))}, straddle +{val(move.get('straddle_up'))} / "
                f"{val(move.get('straddle_down'))}; VIX-implied one-session move "
                f"{val(core.get('vix_session_move'))} pts; realized vol {val(core.get('realized_vol'))}%",
                f"- Straddle theta/day {val(greeks.get('theta_per_day'))}, gamma "
                f"{val(greeks.get('gamma'))}, vega per vol point {val(greeks.get('vega_per_vol_point'))}",
                f"- Past sessions with a similar gap closed: continued "
                f"{val(history.get('continuation_pct'))}%, reversed {val(history.get('reversal_pct'))}%, "
                f"flat {val(history.get('flat_pct'))}% ({val(history.get('sample_size'))} sessions)",
                f"- ATM OI change over 15 min: call {val(oi_ce.get('change_pct'))}%, "
                f"put {val(oi_pe.get('change_pct'))}%; latest-interval volume vs median: call "
                f"{val(spike_ce.get('ratio'))}x, put {val(spike_pe.get('ratio'))}x",
                f"- Historical share of past sessions in which an ATM option bought now and "
                f"held {val(profit.get('horizon_minutes'))} min would have been profitable after "
                f"costs (IV held, {val(profit.get('sessions'))} sessions): call {freq('call')}%, "
                f"put {freq('put')}%, straddle {freq('straddle')}%",
                f"- Time blocks (descriptive history): {val(block_text)}",
            ]
        )
