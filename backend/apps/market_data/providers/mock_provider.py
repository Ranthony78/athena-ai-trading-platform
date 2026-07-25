from datetime import datetime

from .base_provider import BaseMarketProvider


class MockMarketProvider(BaseMarketProvider):
    """
    Mock market data provider for development and testing.
    Returns static dummy data — no real API calls.
    """

    def get_quote(self, symbol: str) -> dict:
        """Return a static mock quote for any symbol."""
        return {
            "symbol": symbol,
            "ltp": 24500.00,
            "open": 24350.00,
            "high": 24600.00,
            "low": 24300.00,
            "close": 24400.00,
            "change": 100.00,
            "change_percent": 0.41,
            "volume": 1254870,
            "oi": 0,
            "bid": 24499.00,
            "ask": 24501.00,
            "timestamp": datetime.now(),
        }

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Return mock quotes for a list of symbols."""
        return [self.get_quote(symbol) for symbol in symbols]

    def get_historical_data(
        self,
        symbol: str,
        interval: str,
        from_date: str = None,
        to_date: str = None,
    ) -> list[dict]:
        """Return empty historical data in mock mode."""
        return []

    def get_option_chain(self, symbol: str) -> list[dict]:
        """Return empty option chain in mock mode."""
        return []