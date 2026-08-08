import logging

from ..repositories.zerodha_repository import ZerodhaConfigRepository
from .mcp_service import ZerodhaKiteMCPService

logger = logging.getLogger(__name__)


class KiteService:
    """
    High-level Zerodha Kite service.
    Wraps ZerodhaKiteMCPService with business logic
    and error handling.
    """

    def __init__(self, user) -> None:
        self.user = user
        self.config = ZerodhaConfigRepository.get_for_user(user)

    def _mcp(self) -> ZerodhaKiteMCPService:
        """Return MCP service instance."""
        return ZerodhaKiteMCPService(self.user)

    # ------------------------------------------------------------------
    # Profile & Funds
    # ------------------------------------------------------------------

    def get_profile(self) -> dict:
        """Fetch user profile from Zerodha."""
        try:
            return self._mcp().get_profile()
        except Exception as e:
            logger.error(f"KiteService get_profile error: {e}")
            return {"error": str(e)}

    def get_funds(self) -> dict:
        """Fetch available funds."""
        try:
            return self._mcp().get_funds()
        except Exception as e:
            logger.error(f"KiteService get_funds error: {e}")
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Market Data
    # ------------------------------------------------------------------

    def get_quote(self, symbol: str) -> dict:
        """Fetch live quote."""
        try:
            return self._mcp().get_quote(symbol)
        except Exception as e:
            logger.error(f"KiteService get_quote error [{symbol}]: {e}")
            return {"error": str(e)}

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Fetch multiple live quotes."""
        try:
            return self._mcp().get_quotes(symbols)
        except Exception as e:
            logger.error(f"KiteService get_quotes error: {e}")
            return []

    def get_historical(
        self,
        instrument_token: int,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[dict]:
        """Fetch historical candle data."""
        try:
            return self._mcp().get_historical_data(
                instrument_token=instrument_token,
                interval=interval,
                from_date=from_date,
                to_date=to_date,
            )
        except Exception as e:
            logger.error(f"KiteService get_historical error: {e}")
            return []

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def get_orders(self) -> list[dict]:
        """Fetch today's orders."""
        try:
            return self._mcp().get_orders()
        except Exception as e:
            logger.error(f"KiteService get_orders error: {e}")
            return []

    def place_order(self, params: dict) -> dict:
        """Place a live order via Zerodha."""
        try:
            return self._mcp().place_order(**params)
        except Exception as e:
            logger.error(f"KiteService place_order error: {e}")
            return {"success": False, "error": str(e)}

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an order."""
        try:
            return self._mcp().cancel_order(order_id)
        except Exception as e:
            logger.error(f"KiteService cancel_order error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Positions & Holdings
    # ------------------------------------------------------------------

    def get_positions(self) -> dict:
        """Fetch current positions."""
        try:
            return self._mcp().get_positions()
        except Exception as e:
            logger.error(f"KiteService get_positions error: {e}")
            return {"error": str(e)}

    def get_holdings(self) -> list[dict]:
        """Fetch holdings."""
        try:
            return self._mcp().get_holdings()
        except Exception as e:
            logger.error(f"KiteService get_holdings error: {e}")
            return []