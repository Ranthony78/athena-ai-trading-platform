import logging
from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from apps.market_data.repositories.instrument_repository import InstrumentRepository

from ..models import PaperAccount, PaperOrder
from ..repositories.paper_repository import (
    PaperAccountRepository,
    PaperOrderRepository,
)
from .broker_simulator import BrokerSimulator
from .position_service import PositionService

logger = logging.getLogger(__name__)


class OrderService:
    """
    Handles paper trading order placement, modification, and cancellation.
    Coordinates with BrokerSimulator for execution.
    """

    def __init__(self) -> None:
        self.simulator = BrokerSimulator()

    def place_order(
        self,
        user,
        symbol: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0,
        product: str = "MIS",
        tag: str = "",
    ) -> dict:
        """
        Place a paper trading order.

        Args:
            user:             Django user
            symbol:           Instrument symbol
            transaction_type: BUY or SELL
            quantity:         Number of units
            order_type:       MARKET or LIMIT
            price:            Limit price (0 for market)
            product:          MIS or NRML
            tag:              Order tag/source

        Returns:
            Order result dict
        """
        # Get or create account
        account, _ = PaperAccountRepository.get_or_create_for_user(user)

        # Get instrument
        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return {
                "success": False,
                "message": f"Instrument not found: {symbol}",
            }

        # Simulate execution
        if order_type == "MARKET":
            execution = self.simulator.execute_market_order(
                symbol=symbol,
                quantity=quantity,
                transaction_type=transaction_type,
            )
        else:
            execution = self.simulator.execute_limit_order(
                symbol=symbol,
                quantity=quantity,
                transaction_type=transaction_type,
                limit_price=Decimal(str(price)),
            )

        # Create order record
        order = PaperOrder.objects.create(
            account=account,
            instrument=instrument,
            order_type=order_type,
            transaction_type=transaction_type,
            product=product,
            quantity=quantity,
            price=Decimal(str(price)),
            average_price=(
                execution["execution_price"]
                if execution["success"] else Decimal("0")
            ),
            filled_quantity=(
                execution["filled_quantity"]
                if execution["success"] else 0
            ),
            pending_quantity=(
                0 if execution["success"] else quantity
            ),
            status="COMPLETE" if execution["success"] else "PENDING",
            execution_time=(
                execution["timestamp"]
                if execution["success"] else None
            ),
            tag=tag,
        )

        # Update position if order executed
        if execution["success"]:
            PositionService.update_position(
                account=account,
                instrument=instrument,
                transaction_type=transaction_type,
                quantity=execution["filled_quantity"],
                execution_price=execution["execution_price"],
                product=product,
                tag=tag,
            )

            # Deduct brokerage from account
            account.balance -= execution["brokerage"]
            account.save()

        return {
            "success": execution["success"],
            "order_id": order.id,
            "status": order.status,
            "execution_price": float(execution["execution_price"]),
            "filled_quantity": execution["filled_quantity"],
            "brokerage": float(execution["brokerage"]),
            "message": execution["message"],
        }

    def cancel_order(self, user, order_id: int) -> dict:
        """Cancel a pending paper order."""
        account, _ = PaperAccountRepository.get_or_create_for_user(user)

        order = PaperOrderRepository.get_by_id(order_id)

        if not order:
            return {"success": False, "message": "Order not found."}

        if order.account != account:
            return {"success": False, "message": "Unauthorized."}

        if order.status not in ("PENDING", "OPEN"):
            return {
                "success": False,
                "message": f"Cannot cancel order with status: {order.status}",
            }

        order.status = "CANCELLED"
        order.save()

        return {
            "success": True,
            "order_id": order.id,
            "message": "Order cancelled.",
        }

    def get_orders(
        self,
        user,
        status: str = None,
    ):
        """Return orders for a user's account."""
        account, _ = PaperAccountRepository.get_or_create_for_user(user)
        return PaperOrderRepository.get_by_account(account, status)

    def get_today_orders(self, user):
        """Return today's orders."""
        account, _ = PaperAccountRepository.get_or_create_for_user(user)
        return PaperOrderRepository.get_today(account)