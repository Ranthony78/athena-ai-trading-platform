from typing import Optional

from django.db.models import QuerySet

from shared.repositories import BaseRepository

from ..models import Candle, Instrument


class CandleRepository(BaseRepository[Candle]):
    """
    Repository for all Candle (OHLCV) database operations.
    """

    model = Candle

    @classmethod
    def get_by_instrument_and_timeframe(
        cls,
        instrument: Instrument,
        timeframe: str,
        limit: int = 100,
    ) -> QuerySet[Candle]:
        """Return candles for an instrument + timeframe."""
        return cls.model.objects.filter(
            instrument=instrument,
            timeframe=timeframe,
        ).order_by("-candle_time")[:limit]

    @classmethod
    def get_by_symbol_and_timeframe(
        cls,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> QuerySet[Candle]:
        """Return candles by symbol string + timeframe."""
        return cls.model.objects.filter(
            instrument__symbol__iexact=symbol,
            timeframe=timeframe,
        ).select_related("instrument").order_by("-candle_time")[:limit]

    @classmethod
    def get_latest(
        cls,
        instrument: Instrument,
        timeframe: str,
    ) -> Optional[Candle]:
        """Return the most recent candle for an instrument + timeframe."""
        return cls.model.objects.filter(
            instrument=instrument,
            timeframe=timeframe,
        ).order_by("-candle_time").first()

    @classmethod
    def get_range(
        cls,
        instrument: Instrument,
        timeframe: str,
        from_time,
        to_time,
    ) -> QuerySet[Candle]:
        """Return candles within a datetime range."""
        return cls.model.objects.filter(
            instrument=instrument,
            timeframe=timeframe,
            candle_time__gte=from_time,
            candle_time__lte=to_time,
        ).order_by("candle_time")

    @classmethod
    def bulk_upsert(
        cls,
        instrument: Instrument,
        timeframe: str,
        candles: list[dict],
    ) -> None:
        """Bulk insert candles, ignoring duplicates."""
        objects = [
            Candle(
                instrument=instrument,
                timeframe=timeframe,
                candle_time=c["candle_time"],
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
            )
            for c in candles
        ]
        cls.model.objects.bulk_create(
            objects,
            batch_size=500,
            ignore_conflicts=True,
        )

    @classmethod
    def delete_by_instrument(
        cls,
        instrument: Instrument,
        timeframe: Optional[str] = None,
    ) -> int:
        """Delete candles for an instrument. Returns deleted count."""
        queryset = cls.model.objects.filter(instrument=instrument)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        count, _ = queryset.delete()
        return count