from typing import Optional
from django.db.models import QuerySet
from django.utils import timezone

from shared.repositories import BaseRepository
from apps.market_data.models import Instrument

from ..models import Strategy, StrategySignal


class SignalRepository(BaseRepository[StrategySignal]):
    """
    Repository for StrategySignal database operations.
    """

    model = StrategySignal

    @classmethod
    def get_active_signals(cls) -> QuerySet[StrategySignal]:
        """Return all currently active signals."""
        return cls.model.objects.filter(
            status="ACTIVE",
        ).select_related("strategy", "instrument")

    @classmethod
    def get_by_instrument(
        cls,
        instrument: Instrument,
        limit: int = 50,
    ) -> QuerySet[StrategySignal]:
        """Return recent signals for an instrument."""
        return cls.model.objects.filter(
            instrument=instrument,
        ).select_related("strategy").order_by("-signal_time")[:limit]

    @classmethod
    def get_by_strategy(
        cls,
        strategy: Strategy,
        limit: int = 50,
    ) -> QuerySet[StrategySignal]:
        """Return recent signals for a strategy."""
        return cls.model.objects.filter(
            strategy=strategy,
        ).select_related("instrument").order_by("-signal_time")[:limit]

    @classmethod
    def get_today(cls) -> QuerySet[StrategySignal]:
        """Return all signals generated today."""
        today = timezone.now().date()
        return cls.model.objects.filter(
            signal_time__date=today,
        ).select_related("strategy", "instrument").order_by("-signal_time")

    @classmethod
    def expire_old_signals(cls) -> int:
        """Mark signals older than today as expired."""
        today = timezone.now().date()
        count = cls.model.objects.filter(
            status="ACTIVE",
            signal_time__date__lt=today,
        ).update(status="EXPIRED")
        return count