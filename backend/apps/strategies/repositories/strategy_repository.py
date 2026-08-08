from django.db.models import QuerySet

from shared.repositories import BaseRepository

from ..models import Strategy


class StrategyRepository(BaseRepository[Strategy]):
    """
    Repository for Strategy database operations.
    """

    model = Strategy

    @classmethod
    def get_enabled(cls) -> QuerySet[Strategy]:
        """Return all enabled active strategies."""
        return cls.model.objects.filter(
            is_enabled=True,
            is_active=True,
        )

    @classmethod
    def get_by_type(cls, strategy_type: str) -> QuerySet[Strategy]:
        """Return strategies of a given type."""
        return cls.model.objects.filter(
            strategy_type=strategy_type,
            is_active=True,
        )

    @classmethod
    def get_by_name(cls, name: str):
        """Return strategy by name."""
        return cls.model.objects.filter(
            name__iexact=name,
        ).first()