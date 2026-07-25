from typing import Optional

from django.db.models import QuerySet

from ..models import Instrument
from ..repositories.instrument_repository import InstrumentRepository


class InstrumentService:
    """
    Business logic for instrument management.
    Handles all instrument lookup, search, and filtering.
    """

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_all() -> QuerySet[Instrument]:
        """Return all active instruments."""
        return InstrumentRepository.active()

    @staticmethod
    def get_by_symbol(symbol: str) -> Optional[Instrument]:
        """Return instrument by symbol."""
        return InstrumentRepository.get_by_symbol(symbol)

    @staticmethod
    def get_by_token(token: int) -> Optional[Instrument]:
        """Return instrument by Zerodha token."""
        return InstrumentRepository.get_by_token(token)

    @staticmethod
    def get_indices() -> QuerySet[Instrument]:
        """Return all index instruments."""
        return InstrumentRepository.get_indices()

    @staticmethod
    def get_options(
        symbol: str,
        option_type: Optional[str] = None,
    ) -> QuerySet[Instrument]:
        """Return options for an underlying symbol."""
        return InstrumentRepository.get_options(symbol, option_type)

    @staticmethod
    def get_futures(symbol: str) -> QuerySet[Instrument]:
        """Return futures for an underlying symbol."""
        return InstrumentRepository.get_futures(symbol)

    @staticmethod
    def search(query: str) -> QuerySet[Instrument]:
        """Search instruments by symbol or trading symbol."""
        return InstrumentRepository.search(query)

    @staticmethod
    def get_by_expiry(expiry) -> QuerySet[Instrument]:
        """Return all instruments for a given expiry date."""
        return InstrumentRepository.get_by_expiry(expiry)

    @staticmethod
    def get_by_exchange(exchange: str) -> QuerySet[Instrument]:
        """Return all active instruments for a given exchange."""
        return InstrumentRepository.get_by_exchange(exchange)