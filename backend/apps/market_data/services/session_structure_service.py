"""
backend/apps/market_data/services/session_structure_service.py

New file.

Reports today's ACTUAL, ALREADY-REALIZED price structure broken into
standard intraday time blocks (09:15-10:30, 10:30-12:00, 12:00-13:30,
13:30-15:30). This is deliberately descriptive, not predictive — a
"time block analysis" that forecasts future-block bias would need real
historical intraday base rates Athena doesn't have (only daily history
is backfilled; see backfill_candles). Predicting it via AI judgment
alone would be exactly the kind of unfounded confidence this project has
been actively removing from its output.

Instead: for any block that has fully or partially elapsed today, this
reports the REAL realized range, direction, and volatility from actual
candles. For any block that hasn't started yet, it reports NA — the
future hasn't happened, so there's nothing real to report.
"""

import logging
from datetime import datetime, time as dtime
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

TIME_BLOCKS = [
    ("09:15", "10:30"),
    ("10:30", "12:00"),
    ("12:00", "13:30"),
    ("13:30", "15:30"),
]


class SessionStructureService:
    """
    Real, descriptive-only intraday structure. Never fabricates a
    forward-looking bias for a block that hasn't happened yet.
    """

    @classmethod
    def get_today_structure(cls, symbol: str, timeframe: str = "5m") -> Optional[list[dict]]:
        try:
            from ..repositories.instrument_repository import InstrumentRepository
            from ..repositories.candle_repository import CandleRepository

            instrument = InstrumentRepository.get_by_symbol(symbol)
            if not instrument:
                return None

            now_ist = datetime.now(IST)
            today = now_ist.date()
            first_block_start = datetime.combine(
                today, dtime.fromisoformat(TIME_BLOCKS[0][0]), tzinfo=IST
            )

            candles = list(
                CandleRepository.model.objects.filter(
                    instrument=instrument,
                    timeframe=timeframe,
                    candle_time__date=today,
                ).order_by("candle_time").values(
                    "candle_time", "open", "high", "low", "close"
                )
            )

            if not candles:
                if now_ist < first_block_start:
                    # Market genuinely hasn't opened yet today. Rather
                    # than four empty "not started" boxes, fall back to
                    # the most recent day that actually has data — real,
                    # not fabricated, and far more useful than blank.
                    fallback = cls._most_recent_trading_day_structure(
                        instrument, timeframe
                    )
                    if fallback:
                        return fallback
                    return [
                        {"window": f"{s}-{e}", "status": "NOT_STARTED"}
                        for s, e in TIME_BLOCKS
                    ]
                # Market should be open (or has been) and there's still
                # no candle data — this is a genuine sync gap, not a
                # normal pre-market state. Surface it distinctly so it
                # doesn't get silently treated the same as "too early".
                logger.warning(
                    f"SessionStructureService: no {timeframe} candles for "
                    f"{symbol} today, but market should be open/have opened "
                    f"— likely a candle-sync gap, not a normal pre-market state."
                )
                return None

            blocks = []
            for start_str, end_str in TIME_BLOCKS:
                start_t = dtime.fromisoformat(start_str)
                end_t = dtime.fromisoformat(end_str)
                block_start_dt = datetime.combine(today, start_t, tzinfo=IST)

                if now_ist < block_start_dt:
                    # Block hasn't started yet — nothing real to report.
                    blocks.append({
                        "window": f"{start_str}-{end_str}",
                        "status": "NOT_STARTED",
                    })
                    continue

                block_candles = [
                    c for c in candles
                    if start_t <= c["candle_time"].astimezone(IST).time() < end_t
                ]
                if not block_candles:
                    blocks.append({
                        "window": f"{start_str}-{end_str}",
                        "status": "NO_DATA",
                    })
                    continue

                open_price = float(block_candles[0]["open"])
                close_price = float(block_candles[-1]["close"])
                high = max(float(c["high"]) for c in block_candles)
                low = min(float(c["low"]) for c in block_candles)
                range_pts = round(high - low, 2)
                move_pts = round(close_price - open_price, 2)

                status = "COMPLETE" if now_ist >= datetime.combine(
                    today, end_t, tzinfo=IST
                ) else "IN_PROGRESS"

                blocks.append({
                    "window": f"{start_str}-{end_str}",
                    "status": status,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "range_pts": range_pts,
                    "move_pts": move_pts,
                    "direction": (
                        "Up" if move_pts > 0 else "Down" if move_pts < 0 else "Flat"
                    ),
                })

            return blocks
        except Exception as e:
            logger.error(f"SessionStructureService error [{symbol}]: {e}")
            return None

    @classmethod
    def _most_recent_trading_day_structure(cls, instrument, timeframe: str) -> Optional[list[dict]]:
        """
        Finds the most recent date with real candles for this instrument
        and computes the same time-block breakdown for that day. Used as
        the closed-market fallback — real, completed data from an actual
        trading day, clearly labeled by the caller as "most recent
        session" rather than presented as if it were today.
        """
        from ..repositories.candle_repository import CandleRepository

        latest = (
            CandleRepository.model.objects.filter(
                instrument=instrument, timeframe=timeframe
            )
            .order_by("-candle_time")
            .values_list("candle_time", flat=True)
            .first()
        )
        if not latest:
            return None

        target_date = latest.astimezone(IST).date()

        candles = list(
            CandleRepository.model.objects.filter(
                instrument=instrument,
                timeframe=timeframe,
                candle_time__date=target_date,
            ).order_by("candle_time").values(
                "candle_time", "open", "high", "low", "close"
            )
        )
        if not candles:
            return None

        blocks = []
        for start_str, end_str in TIME_BLOCKS:
            start_t = dtime.fromisoformat(start_str)
            end_t = dtime.fromisoformat(end_str)

            block_candles = [
                c for c in candles
                if start_t <= c["candle_time"].astimezone(IST).time() < end_t
            ]
            if not block_candles:
                blocks.append({
                    "window": f"{start_str}-{end_str}",
                    "status": "NO_DATA",
                    "reference_date": target_date.isoformat(),
                })
                continue

            open_price = float(block_candles[0]["open"])
            close_price = float(block_candles[-1]["close"])
            high = max(float(c["high"]) for c in block_candles)
            low = min(float(c["low"]) for c in block_candles)
            move_pts = round(close_price - open_price, 2)

            blocks.append({
                "window": f"{start_str}-{end_str}",
                "status": "REFERENCE",  # distinct from COMPLETE — signals
                                         # "this is a past day, not today"
                                         # to the caller/frontend
                "reference_date": target_date.isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "range_pts": round(high - low, 2),
                "move_pts": move_pts,
                "direction": "Up" if move_pts > 0 else "Down" if move_pts < 0 else "Flat",
            })

        return blocks