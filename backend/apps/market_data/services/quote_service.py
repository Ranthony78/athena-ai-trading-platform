from typing import Optional

from ..models import Quote
from ..providers.provider_factory import ProviderFactory
from ..repositories.instrument_repository import InstrumentRepository
from ..repositories.quote_repository import QuoteRepository


class QuoteService:
    """
    Business logic for real-time quote fetching and storage.
    Coordinates between the market data provider and the quote repository.
    """

    def __init__(self, user=None) -> None:
        self.provider = ProviderFactory.get_provider(user=user)

    # ------------------------------------------------------------------
    # Live Quotes (from provider)
    # ------------------------------------------------------------------

    def get_quote(self, symbol: str) -> Optional[dict]:
        """
        Fetch a live quote for a symbol from the active provider.
        Returns raw provider dict — not a DB model.
        """
        return self.provider.get_quote(symbol)

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """
        Fetch live quotes for multiple symbols from the active provider.
        """
        return self.provider.get_quotes(symbols)

    # ------------------------------------------------------------------
    # Persisted Quotes (from DB)
    # ------------------------------------------------------------------

    @staticmethod
    def get_stored_quote(symbol: str) -> Optional[Quote]:
        """Return the last stored quote for a symbol from DB."""
        return QuoteRepository.get_by_symbol(symbol)

    # ------------------------------------------------------------------
    # Upsert (called by live engine on tick)
    # ------------------------------------------------------------------

    @staticmethod
    def upsert_quote(symbol: str, data: dict) -> tuple[Quote, bool]:
        """
        Persist a live quote to the database.
        Creates or updates the quote record for this instrument.
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            raise ValueError(f"Instrument not found: {symbol}")

        return QuoteRepository.upsert(
            instrument=instrument,
            defaults={
                "last_price": data["ltp"],
                "open_price": data["open"],
                "high_price": data["high"],
                "low_price": data["low"],
                "close_price": data["close"],
                "change": data.get("change", 0),
                "change_percent": data.get("change_percent", 0),
                "volume": data.get("volume", 0),
                "oi": data.get("oi", 0),
                "bid": data.get("bid", 0),
                "ask": data.get("ask", 0),
                "bid_qty": data.get("bid_qty", 0),
                "ask_qty": data.get("ask_qty", 0),
            },
        )