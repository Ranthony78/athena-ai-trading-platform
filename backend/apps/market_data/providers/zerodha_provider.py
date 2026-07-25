import logging
from datetime import datetime

from .base_provider import BaseMarketProvider

logger = logging.getLogger(__name__)


class ZerodhaProvider(BaseMarketProvider):
    """
    Zerodha Kite market data provider.
    Uses ZerodhaKiteMCPService for live data.

    Requires:
        - User must be logged in to Zerodha (valid access token)
        - ZerodhaConfig must exist for the user
        - MARKET_PROVIDER = "zerodha" in settings

    Note: This provider requires a user context.
    For system-level calls, use the mock provider.
    """

    def __init__(self, user=None) -> None:
        self.user = user
        self._service = None

    def _get_service(self):
        """Lazy-load the MCP service."""
        if not self._service:
            if not self.user:
                raise ValueError(
                    "ZerodhaProvider requires a user instance. "
                    "Set MARKET_PROVIDER='mock' for system-level calls."
                )
            from apps.zerodha.services.mcp_service import ZerodhaKiteMCPService
            self._service = ZerodhaKiteMCPService(self.user)
        return self._service

    def get_quote(self, symbol: str) -> dict:
        """Fetch live quote from Zerodha."""
        try:
            service = self._get_service()
            raw = service.get_quote(symbol)
            return self._normalize_quote(symbol, raw)
        except Exception as e:
            logger.error(f"ZerodhaProvider get_quote error [{symbol}]: {e}")
            raise

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Fetch live quotes for multiple symbols."""
        try:
            service = self._get_service()
            raw = service.get_quotes(symbols)
            return [
                self._normalize_quote(s, raw.get(s, {}))
                for s in symbols
            ]
        except Exception as e:
            logger.error(f"ZerodhaProvider get_quotes error: {e}")
            raise

    def get_historical_data(
        self,
        symbol: str,
        interval: str,
        from_date: str = None,
        to_date: str = None,
    ) -> list[dict]:
        """Fetch historical OHLCV from Zerodha."""
        try:
            from apps.market_data.repositories.instrument_repository import (
                InstrumentRepository,
            )
            instrument = InstrumentRepository.get_by_symbol(symbol)
            if not instrument:
                raise ValueError(f"Instrument not found: {symbol}")

            service = self._get_service()
            raw = service.get_historical_data(
                instrument_token=instrument.instrument_token,
                interval=self._map_interval(interval),
                from_date=from_date or "",
                to_date=to_date or "",
            )
            return self._normalize_candles(raw)
        except Exception as e:
            logger.error(
                f"ZerodhaProvider get_historical_data error [{symbol}]: {e}"
            )
            raise

    def get_option_chain(self, symbol: str) -> list[dict]:
        """
        Fetch option chain for a symbol.
        Builds from NFO instruments + live quotes.
        """
        try:
            from apps.market_data.repositories.instrument_repository import (
                InstrumentRepository,
            )
            options = InstrumentRepository.get_options(symbol)
            symbols = [o.trading_symbol for o in options[:100]]

            if not symbols:
                return []

            service = self._get_service()
            quotes = service.get_quotes(symbols)

            chain = []
            for opt in options[:100]:
                quote = quotes.get(opt.trading_symbol, {})
                chain.append({
                    "strike": float(opt.strike or 0),
                    "option_type": opt.option_type,
                    "trading_symbol": opt.trading_symbol,
                    "expiry": str(opt.expiry),
                    "ltp": quote.get("last_price", 0),
                    "oi": quote.get("oi", 0),
                    "volume": quote.get("volume", 0),
                    "iv": 0,
                    "delta": 0,
                    "theta": 0,
                })

            return sorted(chain, key=lambda x: x["strike"])

        except Exception as e:
            logger.error(
                f"ZerodhaProvider get_option_chain error [{symbol}]: {e}"
            )
            raise

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_quote(symbol: str, raw: dict) -> dict:
        """Normalize Zerodha quote to standard format."""
        return {
            "symbol": symbol,
            "ltp": raw.get("last_price", 0),
            "open": raw.get("ohlc", {}).get("open", 0),
            "high": raw.get("ohlc", {}).get("high", 0),
            "low": raw.get("ohlc", {}).get("low", 0),
            "close": raw.get("ohlc", {}).get("close", 0),
            "change": raw.get("net_change", 0),
            "change_percent": raw.get("change", 0),
            "volume": raw.get("volume", 0),
            "oi": raw.get("oi", 0),
            "bid": raw.get("depth", {}).get("buy", [{}])[0].get("price", 0),
            "ask": raw.get("depth", {}).get("sell", [{}])[0].get("price", 0),
            "bid_qty": raw.get("depth", {}).get("buy", [{}])[0].get("quantity", 0),
            "ask_qty": raw.get("depth", {}).get("sell", [{}])[0].get("quantity", 0),
            "timestamp": datetime.now(),
        }

    @staticmethod
    def _normalize_candles(raw: list) -> list[dict]:
        """Normalize Zerodha historical candles to standard format."""
        candles = []
        for c in raw:
            candles.append({
                "candle_time": c[0] if isinstance(c, list) else c.get("date"),
                "open": c[1] if isinstance(c, list) else c.get("open"),
                "high": c[2] if isinstance(c, list) else c.get("high"),
                "low": c[3] if isinstance(c, list) else c.get("low"),
                "close": c[4] if isinstance(c, list) else c.get("close"),
                "volume": c[5] if isinstance(c, list) else c.get("volume", 0),
            })
        return candles

    @staticmethod
    def _map_interval(interval: str) -> str:
        """Map internal timeframe to Zerodha interval string."""
        mapping = {
            "1m": "minute",
            "3m": "3minute",
            "5m": "5minute",
            "15m": "15minute",
            "30m": "30minute",
            "1h": "60minute",
            "1d": "day",
        }
        return mapping.get(interval, "day")