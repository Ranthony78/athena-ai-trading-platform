import logging
from typing import Optional

import httpx
from django.conf import settings

from ..repositories.zerodha_repository import ZerodhaConfigRepository

logger = logging.getLogger(__name__)


class ZerodhaKiteMCPService:
    """
    Zerodha Kite integration service.

    IMPORTANT: despite the class name (kept for naming-convention
    continuity — see note below), this talks to Kite Connect's real
    REST API (https://api.kite.trade), NOT the free hosted MCP server
    at mcp.kite.trade. Those are two separate, incompatible systems:

    - mcp.kite.trade: free, no API key needed, but uses its own
      session mechanism that does NOT accept a standard Kite Connect
      access token. Meant for direct AI-assistant use, not for
      powering a separate application like this one.
    - api.kite.trade: the traditional, paid Kite Connect Developer
      API (api_key + api_secret from a Kite Connect app you create
      and subscribe to). This is what this app's login flow
      (auth_service.py) actually obtains a token for, so this is
      the correct API to call with that token.

    DATA methods below (quotes, funds, profile, historical data,
    positions, holdings) call the real Kite Connect REST API.

    ORDER methods (place_order, modify_order, cancel_order, get_orders,
    get_order_history, GTT methods) are UNCHANGED from the original
    MCP-based implementation and still point at self.mcp_url. They are
    intentionally left as-is and not used by this application's data
    features — order placement/execution is out of scope by design.
    """

    KITE_API_URL = "https://api.kite.trade"
    KITE_VERSION = "3"

    def __init__(self, user) -> None:
        self.user = user
        self.config = ZerodhaConfigRepository.get_for_user(user)

        if not self.config:
            raise ValueError("Zerodha not configured for this user.")

        self.mcp_url = self.config.mcp_url
        self.access_token = self.config.access_token
        self.api_key = self.config.api_key

    # ------------------------------------------------------------------
    # Legacy MCP call path — UNCHANGED, used only by order methods below
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        """Build MCP request headers (legacy — order methods only)."""
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
        Call a Zerodha MCP tool. UNCHANGED — legacy path used only by
        order-related methods below, which are not touched or used by
        this application's data features.
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
    # Real Kite Connect REST client — used by data methods below
    # ------------------------------------------------------------------

    def _kite_headers(self) -> dict:
        """Build real Kite Connect REST API headers."""
        return {
            "X-Kite-Version": self.KITE_VERSION,
            "Authorization": f"token {self.api_key}:{self.access_token}",
        }

    def _kite_get(self, path: str, params: dict = None) -> dict:
        """
        Call a real Kite Connect REST GET endpoint.

        Args:
            path:   endpoint path, e.g. '/quote', '/user/margins'
            params: query parameters (lists are sent as repeated keys,
                    matching Kite's expected format for e.g. ?i=A&i=B)

        Returns:
            The 'data' payload from Kite's {"status": "success",
            "data": {...}} response envelope.
        """
        if not self.config.is_token_valid:
            raise ValueError(
                "Zerodha access token is invalid or expired. "
                "Please login again."
            )

        url = f"{self.KITE_API_URL}{path}"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    url,
                    headers=self._kite_headers(),
                    params=params or {},
                )
                response.raise_for_status()
                body = response.json()

            if body.get("status") != "success":
                raise ValueError(
                    f"Kite API error: {body.get('message', 'Unknown error')}"
                )

            return body.get("data", {})

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Kite Connect HTTP error [{path}]: "
                f"{e.response.status_code} — {e.response.text}"
            )
            raise
        except httpx.TimeoutException:
            logger.error(f"Kite Connect timeout [{path}]")
            raise
        except Exception as e:
            logger.error(f"Kite Connect error [{path}]: {e}")
            raise

    # ------------------------------------------------------------------
    # Profile & Funds (real Kite Connect REST API)
    # ------------------------------------------------------------------

    def get_profile(self) -> dict:
        """Fetch Zerodha user profile."""
        return self._kite_get("/user/profile")

    def get_funds(self) -> dict:
        """
        Fetch available funds and margins.
        Returns {"equity": {"available": {...}, "utilised": {...},
        "net": ...}, "commodity": {...}} — the real Kite Connect shape.
        """
        return self._kite_get("/user/margins")

    # ------------------------------------------------------------------
    # Quotes (real Kite Connect REST API)
    # ------------------------------------------------------------------

    def get_quote(self, exchange_symbol: str) -> dict:
        """
        Fetch a full live quote for one instrument.

        Args:
            exchange_symbol: full "EXCHANGE:TRADINGSYMBOL" string,
                e.g. "NSE:NIFTY 50", "BSE:SENSEX". Callers are
                responsible for resolving the correct real Kite
                trading symbol before calling this (see
                ZerodhaProvider, which does this resolution).

        Returns:
            The single instrument's quote dict (last_price, ohlc,
            volume, oi, depth, etc.), or {} if not found.
        """
        data = self._kite_get("/quote", params={"i": [exchange_symbol]})
        return data.get(exchange_symbol, {})

    def get_quotes(self, exchange_symbols: list[str]) -> dict:
        """
        Fetch full live quotes for multiple instruments.

        Args:
            exchange_symbols: list of "EXCHANGE:TRADINGSYMBOL" strings.

        Returns:
            Dict keyed by exchange_symbol, matching Kite's response
            shape directly.
        """
        return self._kite_get("/quote", params={"i": exchange_symbols})

    def get_ohlc(self, exchange_symbols: list[str]) -> dict:
        """Fetch OHLC + LTP snapshots for multiple instruments."""
        return self._kite_get("/quote/ohlc", params={"i": exchange_symbols})

    # ------------------------------------------------------------------
    # Historical Data (real Kite Connect REST API)
    # ------------------------------------------------------------------

    def get_historical_data(
        self,
        instrument_token: int,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[dict]:
        """
        Fetch historical OHLCV candles from Kite Connect.

        Args:
            instrument_token: Zerodha instrument token
            interval:         '5minute', '15minute', 'day' etc.
            from_date:        'YYYY-MM-DD'
            to_date:          'YYYY-MM-DD'

        Returns:
            List of [timestamp, open, high, low, close, volume] rows,
            matching Kite Connect's real response shape.
        """
        data = self._kite_get(
            f"/instruments/historical/{instrument_token}/{interval}",
            params={"from": from_date, "to": to_date},
        )
        return data.get("candles", [])

    # ------------------------------------------------------------------
    # Positions & Holdings (real Kite Connect REST API)
    # ------------------------------------------------------------------

    def get_positions(self) -> dict:
        """Fetch current positions (day + net)."""
        return self._kite_get("/portfolio/positions")

    def get_holdings(self) -> list[dict]:
        """Fetch long-term holdings."""
        return self._kite_get("/portfolio/holdings")

    def get_instruments_csv(self, exchange: str = None) -> str:
        """
        Fetch the raw instruments dump CSV from Kite Connect.

        Unlike every other endpoint here, this returns plain CSV text,
        not the usual {"status": "success", "data": {...}} JSON
        envelope — so it can't go through _kite_get().

        Args:
            exchange: optional, e.g. "NFO". If omitted, returns the
                full dump across all exchanges (large — tens of MB).

        Returns:
            Raw CSV text, ready to write straight to a file.
        """
        if not self.config.is_token_valid:
            raise ValueError(
                "Zerodha access token is invalid or expired. "
                "Please login again."
            )

        path = f"/instruments/{exchange}" if exchange else "/instruments"
        url = f"{self.KITE_API_URL}{path}"

        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, headers=self._kite_headers())
            response.raise_for_status()
            return response.text

    # ------------------------------------------------------------------
    # Orders — UNCHANGED, legacy MCP path, not used by this app's
    # data features. Left exactly as originally written.
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
    # GTT Orders — UNCHANGED, legacy MCP path
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