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
    ) -> dict:
        from apps.market_data.services.daily_levels_service import DailyLevelsService
        from apps.market_data.services.futures_service import FuturesService
        from apps.market_data.services.session_metrics_service import SessionMetrics

        quote = quote or {}
        vix = vix or {}

        def safe(label, fn, *args):
            try:
                return fn(*args)
            except Exception as e:
                logger.error(f"DeterministicMetrics {label} error: {e}")
                return None

        spot = quote.get("ltp")
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
        }

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
            ]
        )
