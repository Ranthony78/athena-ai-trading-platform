import logging
from datetime import datetime
from decimal import Decimal

from apps.market_data.repositories.quote_repository import QuoteRepository
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.market_data.providers.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)

# Simulated brokerage per lot
BROKERAGE_PER_ORDER = Decimal("20.00")


class BrokerSimulator:
    """
    Simulates broker order execution for paper trading.
    Uses live/mock quotes to determine execution price.
    """

    def __init__(self, user=None) -> None:
        self.provider = ProviderFactory.get_provider(user=user)

    def get_execution_price(self, symbol: str, order_type: str) -> Decimal:
        """
        Get the price at which a paper order would execute.
        Market orders execute at LTP.
        Limit orders execute at limit price (simplified).
        """
        try:
            quote = self.provider.get_quote(symbol)
            if quote:
                return Decimal(str(quote.get("ltp", 0)))
        except Exception as e:
            logger.error(f"BrokerSimulator price error for {symbol}: {e}")

        # Fallback to stored quote
        stored = QuoteRepository.get_by_symbol(symbol)
        if stored:
            return stored.last_price

        return Decimal("0")

    def execute_market_order(
        self,
        symbol: str,
        quantity: int,
        transaction_type: str,
    ) -> dict:
        """
        Simulate a market order execution.

        Returns:
            {
                "success": bool,
                "execution_price": Decimal,
                "filled_quantity": int,
                "brokerage": Decimal,
                "timestamp": datetime,
                "message": str,
            }
        """
        execution_price = self.get_execution_price(symbol, "MARKET")

        if execution_price <= 0:
            return {
                "success": False,
                "execution_price": Decimal("0"),
                "filled_quantity": 0,
                "brokerage": Decimal("0"),
                "timestamp": datetime.now(),
                "message": f"Could not get execution price for {symbol}",
            }

        return {
            "success": True,
            "execution_price": execution_price,
            "filled_quantity": quantity,
            "brokerage": BROKERAGE_PER_ORDER,
            "timestamp": datetime.now(),
            "message": f"Order executed at {execution_price}",
        }

    def execute_limit_order(
        self,
        symbol: str,
        quantity: int,
        transaction_type: str,
        limit_price: Decimal,
    ) -> dict:
        """
        Simulate a limit order.
        Executes immediately if LTP is within the limit price.
        """
        ltp = self.get_execution_price(symbol, "LIMIT")

        can_execute = (
            (transaction_type == "BUY" and ltp <= limit_price) or
            (transaction_type == "SELL" and ltp >= limit_price)
        )

        if not can_execute:
            return {
                "success": False,
                "execution_price": Decimal("0"),
                "filled_quantity": 0,
                "brokerage": Decimal("0"),
                "timestamp": datetime.now(),
                "message": (
                    f"Limit order pending. "
                    f"LTP: {ltp} | Limit: {limit_price}"
                ),
            }

        execution_price = limit_price

        return {
            "success": True,
            "execution_price": execution_price,
            "filled_quantity": quantity,
            "brokerage": BROKERAGE_PER_ORDER,
            "timestamp": datetime.now(),
            "message": f"Limit order executed at {execution_price}",
        }