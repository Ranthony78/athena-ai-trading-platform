import logging
from decimal import Decimal

from django.db import transaction

from apps.ai_engine.models import AnalysisSession
from apps.market_data.models import Instrument
from apps.market_data.repositories.instrument_repository import InstrumentRepository

from ..models import PaperAccount, PaperOrder, PaperPosition
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

    def __init__(self, user=None) -> None:
        self.user = user
        self.simulator = BrokerSimulator(user=user)

    @transaction.atomic
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
        instrument_id: int = None,
        analysis_session_id: int = None,
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
        account = PaperAccount.objects.select_for_update().get(pk=account.pk)
        if quantity <= 0 or transaction_type not in ("BUY", "SELL"):
            return {
                "success": False,
                "message": "A positive quantity and BUY/SELL direction are required.",
            }

        # Get instrument
        instrument = (
            Instrument.objects.filter(id=instrument_id, is_active=True).first()
            if instrument_id is not None
            else InstrumentRepository.get_by_symbol(symbol)
        )
        if not instrument:
            return {
                "success": False,
                "message": f"Instrument not found: {symbol}",
            }

        current_position = PaperPosition.objects.filter(
            account=account,
            instrument=instrument,
            is_open=True,
        ).first()
        if current_position is not None:
            position_direction = (
                "BUY" if current_position.direction == "LONG" else "SELL"
            )
            if (
                transaction_type != position_direction
                and quantity > current_position.quantity
            ):
                return {
                    "success": False,
                    "message": "This order is larger than the open position. Close it first, then place a separate order for any new exposure.",
                }

        analysis_session = None
        if instrument_id is not None and (
            instrument.exchange != "NFO" or not instrument.option_type
        ):
            return {
                "success": False,
                "message": "Paper option orders require an active NFO option contract.",
            }
        if (
            instrument_id is not None
            and getattr(self.simulator.provider, "data_source", "UNKNOWN") != "ZERODHA"
        ):
            return {
                "success": False,
                "message": "Option paper trades require verified Zerodha quotes; mock or unknown provider prices are not used.",
            }
        if instrument_id is not None and quantity % max(instrument.lot_size, 1):
            return {
                "success": False,
                "message": f"Quantity must be in multiples of {instrument.lot_size} for this option contract.",
            }

        if analysis_session_id is not None:
            analysis_session = AnalysisSession.objects.filter(
                id=analysis_session_id,
                user=user,
                status="COMPLETE",
            ).first()
            if not analysis_session:
                return {
                    "success": False,
                    "message": "The linked AI analysis was not found for this account.",
                }
            try:
                ai_signal = analysis_session.ai_signal
            except Exception:
                ai_signal = None
            volatility_setup = (analysis_session.parsed_output or {}).get(
                "volatility_setup"
            ) or {}
            pair_legs = volatility_setup.get("legs") or []
            pair_instrument_ids = (
                {
                    leg.get("instrument_id")
                    for leg in pair_legs
                    if leg.get("instrument_id") is not None
                }
                if volatility_setup.get("eligible") is True
                else set()
            )
            pair_entry = (
                instrument.id in pair_instrument_ids
                and transaction_type == "BUY"
                and tag == "AI_PAPER_VOLATILITY"
                and (analysis_session.paper_evaluation or {}).get("status")
                == "REQUESTED"
                and current_position is None
            )
            pair_full_close = (
                instrument.id in pair_instrument_ids
                and transaction_type == "SELL"
                and tag == "AI_PAPER_VOLATILITY_EXIT"
                and current_position is not None
                and current_position.direction == "LONG"
                and current_position.analysis_session_id == analysis_session.id
                and current_position.tag == "AI_PAPER_VOLATILITY"
                and quantity == current_position.quantity
            )
            linked_entry = (
                ai_signal
                and ai_signal.option_instrument_id == instrument.id
                and transaction_type == "BUY"
                and (
                    current_position is None
                    or (
                        current_position.direction == "LONG"
                        and current_position.analysis_session_id == analysis_session.id
                    )
                )
            )
            linked_full_close = (
                ai_signal
                and ai_signal.option_instrument_id == instrument.id
                and transaction_type == "SELL"
                and current_position is not None
                and current_position.direction == "LONG"
                and current_position.analysis_session_id == analysis_session.id
                and quantity == current_position.quantity
            )
            if not (linked_entry or linked_full_close or pair_entry or pair_full_close):
                return {
                    "success": False,
                    "message": "This AI-linked paper order must use its exact suggested contract or eligible paper-only pair and open or close the linked long position.",
                }

        # Simulate execution
        if order_type == "MARKET":
            execution = self.simulator.execute_market_order(
                symbol=(
                    instrument.trading_symbol if instrument_id is not None else symbol
                ),
                quantity=quantity,
                transaction_type=transaction_type,
            )
        else:
            execution = self.simulator.execute_limit_order(
                symbol=(
                    instrument.trading_symbol if instrument_id is not None else symbol
                ),
                quantity=quantity,
                transaction_type=transaction_type,
                limit_price=Decimal(str(price)),
            )

        increasing = current_position is None or transaction_type == (
            "BUY" if current_position.direction == "LONG" else "SELL"
        )
        if (
            execution["success"]
            and increasing
            and execution["execution_price"] * quantity + execution["brokerage"]
            > account.balance - account.used_margin
        ):
            return {
                "success": False,
                "message": "Insufficient simulated available balance for this paper entry and its costs.",
            }

        # Create order record
        order = PaperOrder.objects.create(
            account=account,
            instrument=instrument,
            analysis_session=analysis_session,
            order_type=order_type,
            transaction_type=transaction_type,
            product=product,
            quantity=quantity,
            price=Decimal(str(price)),
            average_price=(
                execution["execution_price"] if execution["success"] else Decimal("0")
            ),
            filled_quantity=(
                execution["filled_quantity"] if execution["success"] else 0
            ),
            pending_quantity=(0 if execution["success"] else quantity),
            status=(
                "COMPLETE"
                if execution["success"]
                else "REJECTED" if order_type == "MARKET" else "PENDING"
            ),
            execution_time=(execution["timestamp"] if execution["success"] else None),
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
                analysis_session=analysis_session,
                order_brokerage=execution["brokerage"],
            )

            # Deduct brokerage from account
            account.balance -= execution["brokerage"]
            account.total_pnl -= execution["brokerage"]
            account.today_pnl -= execution["brokerage"]
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
