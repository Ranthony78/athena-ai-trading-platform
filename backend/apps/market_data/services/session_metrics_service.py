"""
Small, pure session metrics: gap retrace, up/down-bar volume confirmation,
and percentage change. No I/O, so each is exactly testable. Every function
returns None when its inputs cannot support an honest answer.
"""

from typing import Optional

FLAT_GAP_BAND_PCT = 0.10  # gaps smaller than this are treated as no gap


class SessionMetrics:

    @staticmethod
    def pct_change(
        previous: Optional[float], current: Optional[float]
    ) -> Optional[float]:
        """Percentage change from `previous` to `current`; None on bad input."""
        try:
            previous, current = float(previous), float(current)
        except (TypeError, ValueError):
            return None
        if previous <= 0 or current <= 0:
            return None
        return round((current - previous) / previous * 100, 2)

    @classmethod
    def gap_retrace(
        cls,
        previous_close: Optional[float],
        session_open: Optional[float],
        price: Optional[float],
        flat_band_pct: float = FLAT_GAP_BAND_PCT,
    ) -> Optional[dict]:
        """
        How much of today's opening gap price has given back, 0-100%.
        100 means the gap is fully filled (price is at or beyond the
        previous close); 0 means price is at or beyond the open, away
        from the close.
        """
        try:
            previous_close = float(previous_close)
            session_open = float(session_open)
            price = float(price)
        except (TypeError, ValueError):
            return None
        if min(previous_close, session_open, price) <= 0:
            return None

        gap_points = session_open - previous_close
        gap_pct = gap_points / previous_close * 100
        if abs(gap_pct) < flat_band_pct:
            return {
                "direction": "FLAT",
                "gap_points": round(gap_points, 2),
                "gap_pct": round(gap_pct, 2),
                "retrace_pct": None,
            }

        retraced = (session_open - price) / gap_points * 100
        return {
            "direction": "UP" if gap_points > 0 else "DOWN",
            "gap_points": round(gap_points, 2),
            "gap_pct": round(gap_pct, 2),
            "retrace_pct": round(min(max(retraced, 0.0), 100.0), 1),
        }

    @staticmethod
    def volume_confirmation(
        candles: list[dict], min_candles: int = 5
    ) -> Optional[dict]:
        """
        Volume on up bars versus down bars (oldest first, each with
        open/close/volume). Flat bars are ignored. None when there are
        fewer than `min_candles` bars or no volume at all, as with index
        candles, which carry no volume.
        """
        if len(candles) < min_candles:
            return None
        up = down = 0.0
        for candle in candles:
            try:
                volume = float(candle["volume"])
                change = float(candle["close"]) - float(candle["open"])
            except (KeyError, TypeError, ValueError):
                return None
            if change > 0:
                up += volume
            elif change < 0:
                down += volume
        total = up + down
        if total <= 0:
            return None
        up_share = up / total * 100
        if up_share >= 55:
            verdict = "BUYING"
        elif up_share <= 45:
            verdict = "SELLING"
        else:
            verdict = "BALANCED"
        return {
            "up_volume": int(up),
            "down_volume": int(down),
            "up_share_pct": round(up_share, 1),
            "verdict": verdict,
            "candles": len(candles),
        }
