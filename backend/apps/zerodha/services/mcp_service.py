import logging
from typing import Optional

import httpx
from django.conf import settings

from ..repositories.zerodha_repository import ZerodhaConfigRepository

logger = logging.getLogger(__name__)


class ZerodhaKiteMCPService:
    """
    Zerodha Kite MCP (Model Context Protocol) Service.
    Integrates with the Zerodha MCP server at mcp.kite.trade.

    This is the primary integration point for live data in Sprint 20.
    The MCP server exposes Zerodha Kite tools via the MCP protocol.
    """

    def __init__(self, user) -> None:
        self.user = user
        self.config = ZerodhaConfigRepository.get_for_user(user)

        if not self.config:
            raise ValueError("Zerodha not configured for this user.")

        self.mcp_url = self.config.mcp_url
        self.access_token = self.config.access_token
        self.api_key = self.config.api_key

    def _headers(self) -> dict:
        """Build MCP request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"token {self.api_key}:{self.access_token}",
        }

    def _call(
        self,
        tool: str,
        params: dict = None,
    ) -> dict:
        """
        Call a Zerodha MCP tool.

        Args:
            tool:   MCP tool name e.g. 'get_quote', 'get_holdings'
            params: Tool parameters

        Returns:
            Tool response dict
        """
        if not self.config.is_token_valid:
            raise ValueError(
                "Zerodha access token is invalid or expired. "
                "Please login again."
            )

        payload = {
            "tool": tool,
            "params": params or {},
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.mcp_url,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MCP HTTP error [{tool}]: "
                f"{e.response.status_code} — {e.response.text}"
            )
            raise
        except httpx.TimeoutException:
            logger.error(f"MCP timeout [{tool}]")
            raise
        except Exception as e:
            logger.error(f"MCP error [{tool}]: {e}")
            raise

    # ------------------------------------------------------------------
    # Profile & Funds
    # ------------------------------------------------------------------

    def get_profile(self) -> dict:
        """Fetch Zerodha user profile."""
        return self._call("get_profile")

    def get_funds(self) -> dict:
        """Fetch available funds and margins."""
        return self._call("get_margins")

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------

    def get_quote(self, symbol: str) -> dict:
        """
        Fetch live quote for a symbol.
        Maps to Zerodha's get_ltp or get_quotes tool.
        """
        return self._call(
            "get_ltp",
            {"instruments": [f"NSE:{symbol}"]},
        )

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Fetch live quotes for multiple symbols."""
        instruments = [f"NSE:{s}" for s in symbols]
        return self._call(
            "get_quotes",
            {"instruments": instruments},
        )

    def get_ohlc(self, symbols: list[str]) -> dict:
        """Fetch OHLC data for symbols."""
        instruments = [f"NSE:{s}" for s in symbols]
        return self._call(
            "get_ohlc",
            {"instruments": instruments},
        )

    # ------------------------------------------------------------------
    # Historical Data
    # ------------------------------------------------------------------

    def get_historical_data(
        self,
        instrument_token: int,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[dict]:
        """
        Fetch historical OHLCV candles from Zerodha.

        Args:
            instrument_token: Zerodha instrument token
            interval:         '5minute', '15minute', 'day' etc.
            from_date:        'YYYY-MM-DD'
            to_date:          'YYYY-MM-DD'
        """
        return self._call(
            "get_historical_data",
            {
                "instrument_token": instrument_token,
                "interval": interval,
                "from": from_date,
                "to": to_date,
            },
        )

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def get_orders(self) -> list[dict]:
        """Fetch all orders for today."""
        return self._call("get_orders")

    def get_order_history(self, order_id: str) -> list[dict]:
        """Fetch order history for a specific order."""
        return self._call(
            "get_order_history",
            {"order_id": order_id},
        )

    def place_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        product: str = "MIS",
        price: float = 0,
        trigger_price: float = 0,
        tag: str = "",
    ) -> dict:
        """
        Place an order via Zerodha MCP.
        Only available in live trading mode.
        """
        params = {
            "tradingsymbol": tradingsymbol,
            "exchange": exchange,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "order_type": order_type,
            "product": product,
            "validity": "DAY",
        }

        if order_type == "LIMIT" and price:
            params["price"] = price

        if order_type in ("SL", "SL-M") and trigger_price:
            params["trigger_price"] = trigger_price

        if tag:
            params["tag"] = tag

        return self._call("place_order", params)

    def cancel_order(self, order_id: str, variety: str = "regular") -> dict:
        """Cancel an order."""
        return self._call(
            "cancel_order",
            {"order_id": order_id, "variety": variety},
        )

    def modify_order(
        self,
        order_id: str,
        quantity: int = None,
        price: float = None,
        trigger_price: float = None,
        order_type: str = None,
        variety: str = "regular",
    ) -> dict:
        """Modify an existing order."""
        params = {"order_id": order_id, "variety": variety}
        if quantity:
            params["quantity"] = quantity
        if price:
            params["price"] = price
        if trigger_price:
            params["trigger_price"] = trigger_price
        if order_type:
            params["order_type"] = order_type
        return self._call("modify_order", params)

    # ------------------------------------------------------------------
    # Positions & Holdings
    # ------------------------------------------------------------------

    def get_positions(self) -> dict:
        """Fetch current positions (day + net)."""
        return self._call("get_positions")

    def get_holdings(self) -> list[dict]:
        """Fetch long-term holdings."""
        return self._call("get_holdings")

    # ------------------------------------------------------------------
    # GTT Orders
    # ------------------------------------------------------------------

    def get_gtts(self) -> list[dict]:
        """Fetch all GTT (Good Till Triggered) orders."""
        return self._call("get_gtts")

    def place_gtt(
        self,
        trigger_type: str,
        tradingsymbol: str,
        exchange: str,
        trigger_values: list[float],
        last_price: float,
        orders: list[dict],
    ) -> dict:
        """Place a GTT order."""
        return self._call(
            "place_gtt_order",
            {
                "trigger_type": trigger_type,
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "trigger_values": trigger_values,
                "last_price": last_price,
                "orders": orders,
            },
        )