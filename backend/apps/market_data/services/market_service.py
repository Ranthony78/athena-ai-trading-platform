from ..providers.provider_factory import ProviderFactory
from ..repositories.instrument_repository import InstrumentRepository
from ..repositories.market_repository import MarketRepository


class MarketService:
    """
    Facade service for backward-compatible market data access.
    New features should use InstrumentService, QuoteService, CandleService.
    """

    def __init__(self, user=None) -> None:
        self.provider = ProviderFactory.get_provider(user=user)

    # ------------------------------------------------------------------
    # Instrument (delegates to InstrumentRepository)
    # ------------------------------------------------------------------

    @staticmethod
    def get_all():
        """Return all active instruments."""
        return InstrumentRepository.active()

    @staticmethod
    def get(symbol: str):
        """Return instrument by symbol."""
        return InstrumentRepository.get_by_symbol(symbol)

    # ------------------------------------------------------------------
    # Quotes (delegates to provider)
    # ------------------------------------------------------------------

    def quote(self, symbol: str) -> dict:
        """Fetch live quote from provider."""
        return self.provider.get_quote(symbol)

    def quotes(self, symbols: list[str]) -> list[dict]:
        """Fetch live quotes for multiple symbols."""
        return self.provider.get_quotes(symbols)

    # ------------------------------------------------------------------
    # Historical (delegates to provider)
    # ------------------------------------------------------------------

    def historical(
        self,
        symbol: str,
        interval: str,
        from_date: str = None,
        to_date: str = None,
    ) -> list[dict]:
        """Fetch historical OHLCV from provider."""
        return self.provider.get_historical_data(
            symbol=symbol,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
        )

    def option_chain(self, symbol: str, expiry=None) -> list[dict]:
        """Fetch option chain from provider."""
        return self.provider.get_option_chain(symbol, expiry=expiry)