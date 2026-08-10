from datetime import datetime

from .base_provider import BaseMarketProvider

# Approximate relative price levels per instrument, for realistic-looking
# mock data. These are illustrative only — not live prices. Adjust as
# needed; the point is that instruments no longer look identical.
MOCK_BASE_PRICES = {
    "NIFTY": 24500.00,
    "NIFTY50": 24500.00,
    "BANKNIFTY": 52000.00,
    "FINNIFTY": 23500.00,
    "MIDCPNIFTY": 13000.00,
    "SENSEX": 80500.00,
}

DEFAULT_BASE_PRICE = 1000.00


class MockMarketProvider(BaseMarketProvider):
    """
    Mock market data provider for development and testing.
    Returns static, symbol-aware dummy data — no real API calls.

    Prices are deterministic (not random) so tests relying on this
    provider stay stable across runs. They are NOT live prices.
    """

    def get_quote(self, symbol: str) -> dict:
        """Return a static mock quote scaled to the given symbol."""
        base = MOCK_BASE_PRICES.get(symbol.upper(), DEFAULT_BASE_PRICE)

        open_price = round(base * 0.994, 2)
        high_price = round(base * 1.004, 2)
        low_price = round(base * 0.988, 2)
        close_price = round(base * 0.996, 2)
        change = round(base - close_price, 2)
        change_percent = round((change / close_price) * 100, 2) if close_price else 0.0

        return {
            "symbol": symbol,
            "ltp": base,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "change": change,
            "change_percent": change_percent,
            "volume": 1254870,
            "oi": 0,
            "bid": round(base - 1, 2),
            "ask": round(base + 1, 2),
            "timestamp": datetime.now().isoformat(),
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

    def get_option_chain(self, symbol: str, expiry=None) -> list[dict]:
        """Return empty option chain in mock mode."""
        return []
