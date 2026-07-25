import logging
from decimal import Decimal

from ..repositories.paper_repository import (
    PaperAccountRepository,
    PaperPositionRepository,
    PaperTradeRepository,
)

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Provides portfolio summary, PnL, and performance statistics.
    """

    @staticmethod
    def get_portfolio(user) -> dict:
        """
        Return full portfolio summary for a user.
        """
        account, _ = PaperAccountRepository.get_or_create_for_user(user)
        positions = PaperPositionRepository.get_open_positions(account)
        stats = PaperTradeRepository.get_stats(account)

        # Calculate total unrealized PnL
        total_unrealized = sum(
            float(p.unrealized_pnl) for p in positions
        )

        return {
            "account": {
                "balance": float(account.balance),
                "initial_balance": float(account.initial_balance),
                "used_margin": float(account.used_margin),
                "available_balance": account.available_balance,
                "total_pnl": float(account.total_pnl),
                "today_pnl": float(account.today_pnl),
                "total_return_pct": account.total_return_pct,
                "win_rate": account.win_rate,
            },
            "positions": {
                "open_count": positions.count(),
                "total_unrealized_pnl": round(total_unrealized, 2),
            },
            "trades": stats,
        }

    @staticmethod
    def reset_account(user) -> dict:
        """
        Reset paper trading account to initial state.
        Closes all positions and resets balance.
        """
        account, _ = PaperAccountRepository.get_or_create_for_user(user)

        # Close all open positions
        PaperPositionRepository.filter(
            account=account,
            is_open=True,
        ).update(is_open=False)

        # Reset account
        account.balance = account.initial_balance
        account.used_margin = Decimal("0")
        account.total_pnl = Decimal("0")
        account.today_pnl = Decimal("0")
        account.total_trades = 0
        account.winning_trades = 0
        account.losing_trades = 0
        account.save()

        return {
            "success": True,
            "message": "Account reset successfully.",
            "balance": float(account.balance),
        }

    @staticmethod
    def get_trade_history(user, limit: int = 50):
        """Return completed trade history for a user."""
        account, _ = PaperAccountRepository.get_or_create_for_user(user)
        return PaperTradeRepository.get_by_account(account, limit)

    @staticmethod
    def get_today_trades(user):
        """Return today's completed trades."""
        account, _ = PaperAccountRepository.get_or_create_for_user(user)
        return PaperTradeRepository.get_today(account)