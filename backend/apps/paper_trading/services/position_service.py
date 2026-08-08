import logging
from decimal import Decimal
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
            existing.last_price = execution_price
            existing.save()
            return existing

        else:
            # Opposite direction — reduce or close position
            if quantity >= existing.quantity:
                # Close position fully
                pnl = PositionService._calculate_pnl(
                    direction=existing.direction,
                    quantity=existing.quantity,
                    entry_price=existing.average_price,
                    exit_price=execution_price,
                )

                net_pnl = pnl - BROKERAGE

                # Create trade record
                PaperTrade.objects.create(
                    account=account,
                    instrument=instrument,
                    position=existing,
                    direction=existing.direction,
                    quantity=existing.quantity,
                    entry_price=existing.average_price,
                    exit_price=execution_price,
                    entry_time=existing.open_time,
                    exit_time=timezone.now(),
                    pnl=pnl,
                    pnl_pct=float(pnl / (existing.average_price * existing.quantity) * 100),
                    brokerage=BROKERAGE,
                    net_pnl=net_pnl,
                    product=existing.product,
                    tag=existing.tag,
                )

                # Close position
                existing.is_open = False
                existing.close_time = timezone.now()
                existing.realized_pnl = pnl
                existing.save()

                # Update account. balance was never reduced by margin at
                # open time (see the open-position branch above), so
                # only the realized net P&L is added back here — adding
                # margin too would double-count it in the other direction.
                margin = existing.average_price * existing.quantity
                account.used_margin -= margin
                account.balance += net_pnl
                account.total_pnl += net_pnl
                account.today_pnl += net_pnl
                account.total_trades += 1

                if float(pnl) > 0:
                    account.winning_trades += 1
                else:
                    account.losing_trades += 1

                account.save()

                return existing

            else:
                # Partial close
                pnl = PositionService._calculate_pnl(
                    direction=existing.direction,
                    quantity=quantity,
                    entry_price=existing.average_price,
                    exit_price=execution_price,
                )
                existing.quantity -= quantity
                existing.realized_pnl += pnl
                existing.last_price = execution_price
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
                quote = provider.get_quote(position.instrument.symbol)
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