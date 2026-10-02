import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.market_data.providers.provider_factory import ProviderFactory
from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.market_data.repositories.quote_repository import QuoteRepository

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
        self.slippage_bps = Decimal("0")

    def get_execution_price(
        self, symbol: str, order_type: str, transaction_type: str = None
    ) -> Decimal:
        """
        Get the price at which a paper order would execute.
        Option market orders execute at the ask for buys and bid for sells.
        Non-option orders retain the existing LTP simulation.
        Limit orders execute at limit price (simplified).
        """
        instrument = InstrumentRepository.get_by_trading_symbol(symbol)
        is_option = bool(instrument and instrument.option_type)

        try:
            quote = self.provider.get_quote(symbol)
            if quote:
                price = Decimal(str(quote.get("ltp", 0)))
                if is_option:
                    quote_time = quote.get("timestamp")
                    if not quote_time or self._quote_is_stale(quote_time):
                        logger.warning(
                            "Ignoring stale or undated option quote for paper order [%s]",
                            symbol,
                        )
                        return Decimal("0")
                    try:
                        bid = Decimal(str(quote.get("bid")))
                        ask = Decimal(str(quote.get("ask")))
                    except (TypeError, ValueError, InvalidOperation):
                        return Decimal("0")
                    if (
                        not bid.is_finite()
                        or not ask.is_finite()
                        or bid <= 0
                        or ask < bid
                        or transaction_type not in ("BUY", "SELL")
                    ):
                        return Decimal("0")
                    return ask if transaction_type == "BUY" else bid
                if price > 0:
                    return price
        except Exception as e:
            logger.error(f"BrokerSimulator price error for {symbol}: {e}")

        # A stored quote may be old or synthetic. Option-contract simulations
        # require a current provider quote and must never fall back to it.
        if is_option:
            return Decimal("0")

        # Fallback to stored quote
        stored = QuoteRepository.get_by_symbol(symbol)
        if stored:
            return stored.last_price

        return Decimal("0")

    @staticmethod
    def _quote_is_stale(value) -> bool:
        try:
            quote_time = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if timezone.is_naive(quote_time):
                quote_time = timezone.make_aware(quote_time)
            age = timezone.now() - quote_time
            return age > timedelta(minutes=2) or age < -timedelta(minutes=1)
        except (TypeError, ValueError):
            return True

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
        execution_price = self.get_execution_price(symbol, "MARKET", transaction_type)

        if execution_price <= 0:
            return {
                "success": False,
                "execution_price": Decimal("0"),
                "filled_quantity": 0,
                "brokerage": Decimal("0"),
                "timestamp": datetime.now(),
                "message": f"Could not get execution price for {symbol}",
            }

        execution_price = (
            execution_price
            * (
                Decimal("1")
                + self.slippage_bps
                / Decimal("10000")
                * (1 if transaction_type == "BUY" else -1)
            )
        ).quantize(Decimal("0.01"))
        return {
            "success": True,
            "execution_price": execution_price,
            "filled_quantity": quantity,
            "brokerage": BROKERAGE_PER_ORDER,
            "timestamp": timezone.now(),
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
        An option fills only if the current ask/bid is within the limit;
        other instruments continue to use their LTP.
        """
        ltp = self.get_execution_price(symbol, "LIMIT", transaction_type)

        can_execute = ltp > 0 and (
            (transaction_type == "BUY" and ltp <= limit_price)
            or (transaction_type == "SELL" and ltp >= limit_price)
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
                    f"Reference quote: {ltp} | Limit: {limit_price}"
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
