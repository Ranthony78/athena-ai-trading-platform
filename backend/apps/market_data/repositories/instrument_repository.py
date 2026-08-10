from typing import Optional
from django.db import models
from django.db.models import QuerySet
from shared.repositories import BaseRepository
from ..models import Instrument


class InstrumentRepository(BaseRepository[Instrument]):
    """
    Repository for all Instrument database operations.
    """

    model = Instrument

    # Internal short codes used throughout this app vs. the real name
    # Zerodha's own data uses for the underlying instrument's row.
    # Confirmed by direct query: NIFTY 50's real row has
    # symbol="NIFTY 50" / trading_symbol="NIFTY 50", not "NIFTY" — its
    # own option contracts use the short form "NIFTY", which is a real
    # inconsistency in Zerodha's data model, not something we invented.
    INDEX_SYMBOL_ALIASES = {
        "NIFTY": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
        "FINNIFTY": "NIFTY FIN SERVICE",
        "MIDCPNIFTY": "NIFTY MID SELECT",
        "SENSEX": "SENSEX",
        "VIX": "INDIA VIX",
    }

    @classmethod
    def get_by_symbol(cls, symbol: str) -> Optional[Instrument]:
        """
        Return the underlying instrument by symbol (case-insensitive).
        Resolves known short index codes (NIFTY, BANKNIFTY, etc.) to
        their real Zerodha names first, then matches against both
        `symbol` and `trading_symbol`. Explicitly excludes option/
        futures contracts — every option row also carries its
        underlying's short symbol, so without this exclusion thousands
        of derivative rows are ambiguous candidates for a plain match.
        """
        real_name = cls.INDEX_SYMBOL_ALIASES.get(symbol.upper(), symbol)
        return cls.model.objects.filter(
            models.Q(symbol__iexact=real_name) | models.Q(trading_symbol__iexact=real_name),
            option_type="",
        ).exclude(
            instrument_type="FUT",
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
        expiry=None,
    ) -> QuerySet[Instrument]:
        """
        Return options for a given underlying symbol, ordered by
        expiry then strike. Ordering matters here — callers that
        slice this queryset (e.g. get_option_chain's [:N] cap) need
        the nearest, most relevant contracts first, not an arbitrary
        DB-order slice across every expiry NIFTY has.
        """
        queryset = cls.model.objects.filter(
            symbol__iexact=symbol,
            exchange="NFO",
            is_active=True,
        ).exclude(option_type="").order_by("expiry", "strike")

        if option_type:
            queryset = queryset.filter(option_type__iexact=option_type)

        if expiry:
            queryset = queryset.filter(expiry=expiry)

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