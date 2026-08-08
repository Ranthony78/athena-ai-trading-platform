from typing import Optional

from django.db.models import QuerySet

from shared.repositories import BaseRepository

from ..models import BacktestResult, BacktestRun, BacktestTrade


class BacktestRunRepository(BaseRepository[BacktestRun]):

    model = BacktestRun

    @classmethod
    def get_by_user(
        cls,
        user,
        limit: int = 20,
    ) -> QuerySet[BacktestRun]:
        """Return recent backtest runs for a user."""
        return cls.model.objects.filter(
            user=user,
        ).select_related(
            "strategy", "instrument", "result"
        ).order_by("-created_at")[:limit]

    @classmethod
    def get_by_id_for_user(
        cls,
        user,
        run_id: int,
    ) -> Optional[BacktestRun]:
        """Return a single run owned by the user."""
        return cls.model.objects.filter(
            id=run_id,
            user=user,
        ).select_related(
            "strategy", "instrument", "result"
        ).first()

    @classmethod
    def get_completed(cls, user) -> QuerySet[BacktestRun]:
        """Return completed runs for a user."""
        return cls.model.objects.filter(
            user=user,
            status="COMPLETE",
        ).select_related("strategy", "instrument", "result")


class BacktestTradeRepository(BaseRepository[BacktestTrade]):

    model = BacktestTrade

    @classmethod
    def get_by_run(cls, run: BacktestRun) -> QuerySet[BacktestTrade]:
        """Return all trades for a backtest run."""
        return cls.model.objects.filter(
            run=run,
        ).order_by("entry_time")


class BacktestResultRepository(BaseRepository[BacktestResult]):

    model = BacktestResult

    @classmethod
    def get_by_run(cls, run: BacktestRun) -> Optional[BacktestResult]:
        """Return result for a backtest run."""
        return cls.model.objects.filter(run=run).first()