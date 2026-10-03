from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.market_data.models import Instrument
from shared.repositories import BaseRepository

from ..models import Strategy, StrategySignal


class SignalRepository(BaseRepository[StrategySignal]):
    """
    Repository for StrategySignal database operations.
    """

    model = StrategySignal

    @classmethod
    def visible_to(cls, user) -> QuerySet[StrategySignal]:
        """
        Signals `user` may see: their own, plus legacy signals with no owner
        (created before signals were tied to a user; they hold no private data).
        Other users' signals are never returned.
        """
        return cls.model.objects.filter(Q(user=user) | Q(user__isnull=True))

    @classmethod
    def get_active_signals(cls, user) -> QuerySet[StrategySignal]:
        """Return the user's currently active signals."""
        return (
            cls.visible_to(user)
            .filter(status="ACTIVE")
            .select_related("strategy", "instrument")
        )

    @classmethod
    def get_by_instrument(
        cls,
        user,
        instrument: Instrument,
        limit: int = 50,
    ) -> QuerySet[StrategySignal]:
        """Return the user's recent signals for an instrument."""
        return (
            cls.visible_to(user)
            .filter(instrument=instrument)
            .select_related("strategy")
            .order_by("-signal_time")[:limit]
        )

    @classmethod
    def get_by_strategy(
        cls,
        strategy: Strategy,
        limit: int = 50,
    ) -> QuerySet[StrategySignal]:
        """Return recent signals for a strategy."""
        return (
            cls.model.objects.filter(
                strategy=strategy,
            )
            .select_related("instrument")
            .order_by("-signal_time")[:limit]
        )

    @classmethod
    def get_today(cls, user) -> QuerySet[StrategySignal]:
        """Return the user's signals generated today."""
        # Local (IST) date: signal_time__date is evaluated in TIME_ZONE, so a UTC
        # date would be a day behind between midnight and 05:30 IST.
        today = timezone.localdate()
        return (
            cls.visible_to(user)
            .filter(signal_time__date=today)
            .select_related("strategy", "instrument")
            .order_by("-signal_time")
        )

    @classmethod
    def expire_old_signals(cls) -> int:
        """Mark signals older than today as expired."""
        # Local (IST) date: signal_time__date is evaluated in TIME_ZONE, so a UTC
        # date would be a day behind between midnight and 05:30 IST.
        today = timezone.localdate()
        count = cls.model.objects.filter(
            status="ACTIVE",
            signal_time__date__lt=today,
        ).update(status="EXPIRED")
        return count
