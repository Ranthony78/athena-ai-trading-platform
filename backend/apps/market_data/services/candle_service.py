from typing import Optional

from django.db.models import QuerySet

from ..models import Candle, Instrument
from ..providers.provider_factory import ProviderFactory
from ..repositories.candle_repository import CandleRepository
from ..repositories.instrument_repository import InstrumentRepository


class CandleService:
    """
    Business logic for historical OHLCV candle data.
    Coordinates between the provider and candle repository.
    """

    def __init__(self) -> None:
        self.provider = ProviderFactory.get_provider()

    # ------------------------------------------------------------------
    # Fetch from Provider
    # ------------------------------------------------------------------

    def fetch_historical(
        self,
        symbol: str,
        interval: str,
        from_date: str = None,
        to_date: str = None,
    ) -> list[dict]:
        """
        Fetch historical OHLCV data from the active provider.
        Returns raw list of candle dicts.
        """
        return self.provider.get_historical_data(
            symbol=symbol,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
        )

    # ------------------------------------------------------------------
    # DB Queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_candles(
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> QuerySet[Candle]:
        """Return stored candles for a symbol and timeframe."""
        return CandleRepository.get_by_symbol_and_timeframe(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    @staticmethod
    def get_latest(symbol: str, timeframe: str) -> Optional[Candle]:
        """Return the most recent stored candle."""
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return None
        return CandleRepository.get_latest(instrument, timeframe)

    @staticmethod
    def get_range(
        symbol: str,
        timeframe: str,
        from_time,
        to_time,
    ) -> QuerySet[Candle]:
        """Return candles within a datetime range."""
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return Candle.objects.none()
        return CandleRepository.get_range(
            instrument=instrument,
            timeframe=timeframe,
            from_time=from_time,
            to_time=to_time,
        )

    # ------------------------------------------------------------------
    # Persist to DB
    # ------------------------------------------------------------------

    def fetch_and_store(
        self,
        symbol: str,
        timeframe: str,
        from_date: str = None,
        to_date: str = None,
    ) -> int:
        """
        Fetch candles from provider and bulk upsert to DB.
        Returns count of candles stored.
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            raise ValueError(f"Instrument not found: {symbol}")

        candles = self.provider.get_historical_data(
            symbol=symbol,
            interval=timeframe,
            from_date=from_date,
            to_date=to_date,
        )

        if not candles:
            return 0

        CandleRepository.bulk_upsert(
            instrument=instrument,
            timeframe=timeframe,
            candles=candles,
        )

        return len(candles)