"""
Time-block analysis: how each part of the trading day has behaved over the
stored sessions, from 15-minute candles.

For every window and session we take the window's open, high, low and
close, then summarise across sessions: average range, average net move,
how often the window finished up, and how directional it was (net move
divided by range). Labels are descriptive and relative to the other
windows; they are not predictions. A window with too few complete sessions
is reported without labels, and one with a thin sample is flagged.
"""

import logging
from collections import defaultdict
from datetime import time
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
CANDLE_MINUTES = 15
SESSIONS_TO_USE = 20
MIN_SESSIONS = 5  # below this a window gets no labels at all
LOW_CONFIDENCE_SESSIONS = 10
MAX_DATA_AGE_DAYS = 7  # newer data than this is not flagged stale
MIN_COVERAGE = 0.8  # share of a window's candles that must be present

WINDOWS = [
    ("09:15 – 10:30", time(9, 15), time(10, 30)),
    ("10:30 – 12:00", time(10, 30), time(12, 0)),
    ("12:00 – 13:30", time(12, 0), time(13, 30)),
    ("13:30 – 15:30", time(13, 30), time(15, 30)),
]

LEAN_SHARE = 60.0  # percent of sessions the window must favour one way
STRONG_EFFICIENCY = 0.45
MODERATE_EFFICIENCY = 0.25


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _window_stats(candles: list[dict]) -> Optional[dict]:
    first, last = candles[0], candles[-1]
    high = max(c["high"] for c in candles)
    low = min(c["low"] for c in candles)
    if first["open"] <= 0 or high <= low:
        return None
    net = last["close"] - first["open"]
    return {
        "range_pct": (high - low) / first["open"] * 100,
        "net_pct": net / first["open"] * 100,
        "efficiency": abs(net) / (high - low),
    }


def analyse(candles: list[dict], sessions: int = SESSIONS_TO_USE) -> list[dict]:
    """
    candles: [{"time": aware datetime, "open", "high", "low", "close"}],
    any order. Returns one entry per window, in day order.
    """
    by_day: dict = defaultdict(list)
    for candle in candles:
        local = candle["time"].astimezone(IST)
        by_day[local.date()].append((local, candle))

    per_window: dict[str, list[dict]] = {name: [] for name, _, _ in WINDOWS}
    for day in sorted(by_day)[-sessions:]:
        items = sorted(by_day[day], key=lambda pair: pair[0])
        for name, start, end in WINDOWS:
            start_m, end_m = _minutes(start), _minutes(end)
            inside = [
                candle
                for local, candle in items
                if start_m <= _minutes(local.time()) < end_m
            ]
            needed = (end_m - start_m) / CANDLE_MINUTES * MIN_COVERAGE
            if len(inside) < needed:
                continue
            stats = _window_stats(inside)
            if stats:
                per_window[name].append(stats)

    results = []
    for name, start, end in WINDOWS:
        rows = per_window[name]
        hours = (_minutes(end) - _minutes(start)) / 60
        entry = {
            "window": name,
            "sessions": len(rows),
            "low_confidence": len(rows) < LOW_CONFIDENCE_SESSIONS,
            "avg_range_pct": None,
            "avg_net_pct": None,
            "up_share_pct": None,
            "range_per_hour_pct": None,
            "bias": None,
            "volatility": None,
            "trend_strength": None,
        }
        if len(rows) >= MIN_SESSIONS:
            n = len(rows)
            avg_range = sum(r["range_pct"] for r in rows) / n
            avg_net = sum(r["net_pct"] for r in rows) / n
            up_share = sum(1 for r in rows if r["net_pct"] > 0) / n * 100
            efficiency = sum(r["efficiency"] for r in rows) / n
            entry.update(
                avg_range_pct=round(avg_range, 2),
                avg_net_pct=round(avg_net, 2),
                up_share_pct=round(up_share, 1),
                range_per_hour_pct=round(avg_range / hours, 3),
                trend_strength=(
                    "Strong"
                    if efficiency >= STRONG_EFFICIENCY
                    else "Moderate" if efficiency >= MODERATE_EFFICIENCY else "Weak"
                ),
            )
            if up_share >= LEAN_SHARE and avg_net > 0:
                entry["bias"] = "Leans up"
            elif up_share <= 100 - LEAN_SHARE and avg_net < 0:
                entry["bias"] = "Leans down"
            else:
                entry["bias"] = "No consistent lean"
        results.append(entry)

    # Volatility is relative: ranked by range per hour among the windows
    # that have enough data.
    ranked = sorted(
        (e for e in results if e["range_per_hour_pct"] is not None),
        key=lambda e: e["range_per_hour_pct"],
    )
    for index, entry in enumerate(ranked):
        if len(ranked) < 3:
            entry["volatility"] = "Moderate"
        elif index == len(ranked) - 1:
            entry["volatility"] = "High"
        elif index == 0:
            entry["volatility"] = "Low"
        else:
            entry["volatility"] = "Moderate"
    return results


class TimeBlockService:

    @staticmethod
    def build(symbol: str) -> Optional[dict]:
        from django.utils import timezone

        from ..repositories.candle_repository import CandleRepository
        from ..repositories.instrument_repository import InstrumentRepository

        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return None
        # Roughly 26 fifteen-minute candles a day.
        rows = CandleRepository.get_by_instrument_and_timeframe(
            instrument, "15m", limit=SESSIONS_TO_USE * 26 + 26
        )
        candles = [
            {
                "time": r.candle_time,
                "open": float(r.open),
                "high": float(r.high),
                "low": float(r.low),
                "close": float(r.close),
            }
            for r in rows
        ]
        blocks = analyse(candles)
        through = max((c["time"].astimezone(IST).date() for c in candles), default=None)
        age = (timezone.localdate() - through).days if through else None
        return {
            "blocks": blocks,
            "through": through.isoformat() if through else None,
            "stale": age is None or age > MAX_DATA_AGE_DAYS,
            "sessions_requested": SESSIONS_TO_USE,
            "basis": (
                "Descriptive statistics from stored 15-minute candles. Volatility is "
                "relative to the other windows. Not a forecast."
            ),
        }
