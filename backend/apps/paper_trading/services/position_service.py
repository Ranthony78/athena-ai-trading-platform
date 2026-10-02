import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from django.utils import timezone

from ..models import PaperAccount, PaperPosition, PaperTrade
from ..repositories.paper_repository import (
    PaperPositionRepository,
    PaperAccountRepository,
)

logger = logging.getLogger(__name__)

BROKERAGE = Decimal("20.00")


class PositionService:
    """
    Manages paper trading positions.
    Creates, updates, and closes positions on order execution.
    """

    @staticmethod
    def update_position(
        account: PaperAccount,
        instrument,
        transaction_type: str,
        quantity: int,
        execution_price: Decimal,
        product: str = "MIS",
        tag: str = "",
        analysis_session=None,
        order_brokerage: Decimal = None,
    ) -> PaperPosition:
        """
        Create or update a position after order execution.

        - BUY  on no position → opens LONG position
        - SELL on no position → opens SHORT position
        - BUY  on SHORT       → reduces/closes short
        - SELL on LONG        → reduces/closes long
        """
        existing = PaperPositionRepository.get_by_instrument(
            account=account,
            instrument=instrument,
        )

        direction = "LONG" if transaction_type == "BUY" else "SHORT"

        if not existing:
            # Open new position
            position = PaperPosition.objects.create(
                account=account,
                instrument=instrument,
                direction=direction,
                quantity=quantity,
                average_price=execution_price,
                last_price=execution_price,
                product=product,
                tag=tag,
                analysis_session=analysis_session,
                entry_brokerage=order_brokerage or Decimal("0"),
            )

            # Reserve margin. Note: balance is intentionally NOT reduced
            # here — used_margin alone tracks what's locked, so that
            # available_balance (= balance - used_margin) is correct
            # rather than double-counting the same margin.
            margin = execution_price * quantity
            account.used_margin += margin
            account.save()

            return position

        # Existing position
        if existing.direction == direction:
            # Add to position — recalculate average price
            total_qty = existing.quantity + quantity
            total_cost = (
                existing.average_price * existing.quantity +
                execution_price * quantity
            )
            existing.average_price = total_cost / total_qty
            existing.quantity = total_qty
            existing.entry_brokerage += order_brokerage or Decimal("0")
            # Preserve the attribution only while it remains unambiguous.
            # If a position combines entries from different sessions (or
            # manual entries), do not credit one forecast with the whole trade.
            if existing.analysis_session_id != getattr(analysis_session, "id", None):
                existing.analysis_session = None
            existing.last_price = execution_price
            existing.save()
            account.used_margin += execution_price * quantity
            account.save()
            return existing

        else:
            # Opposite direction — reduce or close position
            close_quantity = min(quantity, existing.quantity)
            pnl = PositionService._calculate_pnl(
                direction=existing.direction,
                quantity=close_quantity,
                entry_price=existing.average_price,
                exit_price=execution_price,
            )
            is_full_close = close_quantity == existing.quantity
            allocated_entry_brokerage = (
                existing.entry_brokerage
                if is_full_close
                else (existing.entry_brokerage * Decimal(close_quantity) / Decimal(existing.quantity))
                .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
            exit_brokerage = order_brokerage if order_brokerage is not None else BROKERAGE
            total_brokerage = allocated_entry_brokerage + exit_brokerage
            net_pnl = pnl - total_brokerage

            # Record each realized close fill. The optional FK supports
            # partial exits while keeping the forecast attribution intact.
            PaperTrade.objects.create(
                account=account,
                instrument=instrument,
                position=existing,
                direction=existing.direction,
                quantity=close_quantity,
                entry_price=existing.average_price,
                exit_price=execution_price,
                entry_time=existing.open_time,
                exit_time=timezone.now(),
                pnl=pnl,
                pnl_pct=float(pnl / (existing.average_price * close_quantity) * 100),
                brokerage=total_brokerage,
                net_pnl=net_pnl,
                product=existing.product,
                tag=existing.tag,
                analysis_session=existing.analysis_session,
                ai_signal=(
                    "BOTH" if existing.tag == "AI_PAPER_VOLATILITY"
                    else existing.analysis_session.ai_signal.signal
                    if existing.analysis_session_id else ""
                ),
            )

            margin = existing.average_price * close_quantity
            account.used_margin -= margin
            # In the regular order flow, the order's commission is charged
            # just after this method. Direct callers include it here.
            realized_account_pnl = pnl if order_brokerage is not None else net_pnl
            account.balance += realized_account_pnl
            account.total_pnl += realized_account_pnl
            account.today_pnl += realized_account_pnl
            account.total_trades += 1
            if net_pnl > 0:
                account.winning_trades += 1
            elif net_pnl < 0:
                account.losing_trades += 1
            account.save()

            existing.quantity -= close_quantity
            existing.entry_brokerage -= allocated_entry_brokerage
            existing.realized_pnl += pnl
            existing.last_price = execution_price
            if is_full_close:
                existing.is_open = False
                existing.close_time = timezone.now()
            existing.save()
            return existing

    @staticmethod
    def _calculate_pnl(
        direction: str,
        quantity: int,
        entry_price: Decimal,
        exit_price: Decimal,
    ) -> Decimal:
        """Calculate PnL for a trade."""
        if direction == "LONG":
            return (exit_price - entry_price) * quantity
        else:
            return (entry_price - exit_price) * quantity

    @staticmethod
    def update_unrealized_pnl(account: PaperAccount) -> None:
        """
        Update unrealized PnL for all open positions.
        Called periodically by the market engine.
        """
        from apps.market_data.providers.provider_factory import ProviderFactory

        provider = ProviderFactory.get_provider(user=account.user)
        positions = PaperPositionRepository.get_open_positions(account)

        for position in positions:
            try:
                quote_symbol = (
                    position.instrument.trading_symbol
                    if position.instrument.option_type
                    else position.instrument.symbol
                )
                quote = provider.get_quote(quote_symbol)
                if quote:
                    ltp = Decimal(str(quote["ltp"]))
                    position.last_price = ltp
                    position.unrealized_pnl = PositionService._calculate_pnl(
                        direction=position.direction,
                        quantity=position.quantity,
                        entry_price=position.average_price,
                        exit_price=ltp,
                    )
                    position.save()
            except Exception as e:
                logger.error(
                    f"PnL update error for {position.instrument.symbol}: {e}"
                )

    @staticmethod
    def get_open_positions(user):
        """Return open positions for a user."""
        account, _ = PaperAccountRepository.get_or_create_for_user(user)
        return PaperPositionRepository.get_open_positions(account)
