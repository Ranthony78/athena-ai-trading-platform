"""
Daily support/resistance levels (classic pivots and CPR) from the previous
completed trading session.

The per-row PivotPoints/CPR indicators pivot off the previous *candle* of
whatever timeframe they are given, so on 15-minute data they describe the
last 15 minutes, not yesterday. Traders' pivots come from the prior day's
high/low/close, which is what this service provides.
"""

from typing import Optional

from django.utils import timezone

from ..indicators.pivot import CPR, PivotPoints
from ..repositories.candle_repository import CandleRepository
from ..repositories.instrument_repository import InstrumentRepository

# A weekend plus a long holiday stretch; anything older is stale data and must
# not be presented as the previous session.
MAX_SESSION_AGE_DAYS = 7


class DailyLevelsService:

    @staticmethod
    def previous_session_hlc(symbol: str, session_date=None) -> Optional[dict]:
        """
        High/low/close of the latest stored daily candle dated before
        `session_date` (default: today in IST). None when there is no such
        candle or its values are unusable; never guessed.
        """
        session_date = session_date or timezone.localdate()
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return None

        candles = CandleRepository.get_by_instrument_and_timeframe(
            instrument=instrument, timeframe="1d", limit=5
        )
        for candle in candles:
            candle_date = timezone.localtime(candle.candle_time).date()
            if candle_date >= session_date:
                continue
            if (session_date - candle_date).days > MAX_SESSION_AGE_DAYS:
                return None
            high, low, close = (
                float(candle.high),
                float(candle.low),
                float(candle.close),
            )
            if min(high, low, close) <= 0 or high < low:
                return None
            return {
                "date": candle_date.isoformat(),
                "high": high,
                "low": low,
                "close": close,
            }
        return None

    @classmethod
    def levels(cls, symbol: str, session_date=None) -> Optional[dict]:
        """{'pivot': {...}, 'cpr': {...}, 'based_on': {...}} or None."""
        hlc = cls.previous_session_hlc(symbol, session_date)
        if not hlc:
            return None
        args = (hlc["high"], hlc["low"], hlc["close"])
        return {
            "pivot": PivotPoints.from_prior_session(*args),
            "cpr": CPR.from_prior_session(*args),
            "based_on": hlc,
        }
