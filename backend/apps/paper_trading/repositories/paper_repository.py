from typing import Optional

from django.db.models import QuerySet, Sum
from django.utils import timezone

from shared.repositories import BaseRepository

from ..models import PaperAccount, PaperOrder, PaperPosition, PaperTrade


class PaperAccountRepository(BaseRepository[PaperAccount]):

    model = PaperAccount

    @classmethod
    def get_by_user(cls, user) -> Optional[PaperAccount]:
        """Return paper account for a user."""
        return cls.model.objects.filter(user=user).first()

    @classmethod
    def get_or_create_for_user(cls, user) -> tuple[PaperAccount, bool]:
        """Get or create paper account for a user."""
        return cls.model.objects.get_or_create(user=user)


class PaperOrderRepository(BaseRepository[PaperOrder]):

    model = PaperOrder

    @classmethod
    def get_by_account(
        cls,
        account: PaperAccount,
        status: str = None,
    ) -> QuerySet[PaperOrder]:
        """Return orders for an account, optionally filtered by status."""
        qs = cls.model.objects.filter(
            account=account,
        ).select_related("instrument")

        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-order_time")

    @classmethod
    def get_open_orders(cls, account: PaperAccount) -> QuerySet[PaperOrder]:
        """Return all open/pending orders for an account."""
        return cls.model.objects.filter(
            account=account,
            status__in=["PENDING", "OPEN"],
        ).select_related("instrument")

    @classmethod
    def get_today(cls, account: PaperAccount) -> QuerySet[PaperOrder]:
        """Return today's orders for an account."""
        today = timezone.now().date()
        return cls.model.objects.filter(
            account=account,
            order_time__date=today,
        ).select_related("instrument").order_by("-order_time")

    @classmethod
    def delete_all_for_account(cls, account) -> int:
        """Delete all orders for an account. Used by account reset."""
        deleted, _ = cls.model.objects.filter(account=account).delete()
        return deleted

class PaperPositionRepository(BaseRepository[PaperPosition]):

    model = PaperPosition

    @classmethod
    def get_open_positions(
        cls,
        account: PaperAccount,
    ) -> QuerySet[PaperPosition]:
        """Return all open positions for an account."""
        return cls.model.objects.filter(
            account=account,
            is_open=True,
        ).select_related("instrument")

    @classmethod
    def get_by_instrument(
        cls,
        account: PaperAccount,
        instrument,
    ) -> Optional[PaperPosition]:
        """Return open position for a specific instrument."""
        return cls.model.objects.filter(
            account=account,
            instrument=instrument,
            is_open=True,
        ).first()

    @classmethod
    def delete_all_for_account(cls, account) -> int:
        """Delete all positions for an account. Used by account reset."""
        deleted, _ = cls.model.objects.filter(account=account).delete()
        return deleted

class PaperTradeRepository(BaseRepository[PaperTrade]):

    model = PaperTrade

    @classmethod
    def get_by_account(
        cls,
        account: PaperAccount,
        limit: int = 50,
    ) -> QuerySet[PaperTrade]:
        """Return recent trades for an account."""
        return cls.model.objects.filter(
            account=account,
        ).select_related("instrument").order_by("-exit_time")[:limit]

    @classmethod
    def get_today(cls, account: PaperAccount) -> QuerySet[PaperTrade]:
        """Return today's completed trades."""
        today = timezone.now().date()
        return cls.model.objects.filter(
            account=account,
            exit_time__date=today,
        ).select_related("instrument").order_by("-exit_time")

    @classmethod
    def get_stats(cls, account: PaperAccount) -> dict:
        """Return aggregated trade statistics."""
        trades = cls.model.objects.filter(account=account)
        total = trades.count()

        if total == 0:
            return {
                "total": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
            }

        wins = trades.filter(pnl__gt=0).count()
        losses = trades.filter(pnl__lte=0).count()
        total_pnl = trades.aggregate(
            total=Sum("net_pnl")
        )["total"] or 0

        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total * 100, 2),
            "total_pnl": float(total_pnl),
            "avg_pnl": round(float(total_pnl) / total, 2),
        }

    @classmethod
    def delete_all_for_account(cls, account) -> int:
        """Delete all trade records for an account. Used by account reset."""
        deleted, _ = cls.model.objects.filter(account=account).delete()
        return deleted