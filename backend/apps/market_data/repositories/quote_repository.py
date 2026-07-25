from typing import Optional

from django.db.models import QuerySet

from shared.repositories import BaseRepository

from ..models import Instrument, Quote


class QuoteRepository(BaseRepository[Quote]):
    """
    Repository for all Quote database operations.
    """

    model = Quote

    @classmethod
    def get_by_instrument(cls, instrument: Instrument) -> Optional[Quote]:
        """Return quote for a given instrument instance."""
        return cls.model.objects.filter(
            instrument=instrument,
        ).first()

    @classmethod
    def get_by_symbol(cls, symbol: str) -> Optional[Quote]:
        """Return quote by instrument symbol."""
        return cls.model.objects.filter(
            instrument__symbol__iexact=symbol,
        ).select_related("instrument").first()

    @classmethod
    def get_by_token(cls, token: int) -> Optional[Quote]:
        """Return quote by instrument token."""
        return cls.model.objects.filter(
            instrument__instrument_token=token,
        ).select_related("instrument").first()

    @classmethod
    def get_by_symbols(cls, symbols: list[str]) -> QuerySet[Quote]:
        """Return quotes for a list of symbols."""
        return cls.model.objects.filter(
            instrument__symbol__in=[s.upper() for s in symbols],
        ).select_related("instrument")

    @classmethod
    def get_index_quotes(cls) -> QuerySet[Quote]:
        """Return quotes for all index instruments."""
        return cls.model.objects.filter(
            instrument__instrument_type="IDX",
        ).select_related("instrument")

    @classmethod
    def upsert(
        cls,
        instrument: Instrument,
        defaults: dict,
    ) -> tuple[Quote, bool]:
        """Create or update a quote for the given instrument."""
        return cls.model.objects.update_or_create(
            instrument=instrument,
            defaults=defaults,
        )