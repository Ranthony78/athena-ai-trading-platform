from typing import Optional

from django.db.models import QuerySet

from shared.repositories import BaseRepository

from ..models import Instrument


class InstrumentRepository(BaseRepository[Instrument]):
    """
    Repository for all Instrument database operations.
    """

    model = Instrument

    @classmethod
    def get_by_symbol(cls, symbol: str) -> Optional[Instrument]:
        """Return instrument by symbol (case-insensitive)."""
        return cls.model.objects.filter(
            symbol__iexact=symbol,
        ).first()

    @classmethod
    def get_by_token(cls, token: int) -> Optional[Instrument]:
        """Return instrument by Zerodha instrument token."""
        return cls.model.objects.filter(
            instrument_token=token,
        ).first()

    @classmethod
    def get_by_trading_symbol(cls, trading_symbol: str) -> Optional[Instrument]:
        """Return instrument by trading symbol."""
        return cls.model.objects.filter(
            trading_symbol__iexact=trading_symbol,
        ).first()

    @classmethod
    def get_by_exchange(cls, exchange: str) -> QuerySet[Instrument]:
        """Return all active instruments for a given exchange."""
        return cls.model.objects.filter(
            exchange__iexact=exchange,
            is_active=True,
        )

    @classmethod
    def get_indices(cls) -> QuerySet[Instrument]:
        """Return all index instruments."""
        return cls.model.objects.filter(
            instrument_type="IDX",
            is_active=True,
        )

    @classmethod
    def get_options(
        cls,
        symbol: str,
        option_type: Optional[str] = None,
    ) -> QuerySet[Instrument]:
        """Return options for a given underlying symbol."""
        queryset = cls.model.objects.filter(
            symbol__iexact=symbol,
            exchange="NFO",
            is_active=True,
        ).exclude(option_type="")

        if option_type:
            queryset = queryset.filter(option_type__iexact=option_type)

        return queryset

    @classmethod
    def get_futures(cls, symbol: str) -> QuerySet[Instrument]:
        """Return futures contracts for a given underlying symbol."""
        return cls.model.objects.filter(
            symbol__iexact=symbol,
            exchange="NFO",
            instrument_type="FUT",
            is_active=True,
        )

    @classmethod
    def get_by_expiry(cls, expiry) -> QuerySet[Instrument]:
        """Return all instruments for a given expiry date."""
        return cls.model.objects.filter(
            expiry=expiry,
            is_active=True,
        )

    @classmethod
    def search(cls, query: str) -> QuerySet[Instrument]:
        """Search instruments by symbol or trading symbol."""
        return cls.model.objects.filter(
            is_active=True,
        ).filter(
            symbol__icontains=query,
        ) | cls.model.objects.filter(
            is_active=True,
        ).filter(
            trading_symbol__icontains=query,
        )

    @classmethod
    def upsert_from_import(
        cls,
        token: int,
        defaults: dict,
    ) -> tuple[Instrument, bool]:
        """Upsert an instrument during CSV import."""
        return cls.model.objects.update_or_create(
            instrument_token=token,
            defaults=defaults,
        )

    @classmethod
    def deactivate_all(cls) -> int:
        """Mark all instruments inactive before a fresh import."""
        return cls.model.objects.update(is_active=False)