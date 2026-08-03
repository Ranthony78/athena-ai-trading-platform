import logging
import time
from datetime import datetime

from django.utils import timezone

from apps.market_data.repositories.instrument_repository import InstrumentRepository
from apps.strategies.repositories.strategy_repository import StrategyRepository

from ..models import BacktestRun, BacktestTrade
from ..repositories.backtest_repository import (
    BacktestRunRepository,
    BacktestTradeRepository,
)
from .backtest_engine import BacktestEngine
from .report_service import ReportService

logger = logging.getLogger(__name__)


class BacktestService:
    """
    Orchestrates backtest execution.
    Creates run → executes engine → persists trades → generates report.
    """

    @staticmethod
    def create_run(user, data: dict) -> BacktestRun:
        """Create a new backtest run configuration."""
        instrument = InstrumentRepository.get_by_symbol(
            data["symbol"].upper()
        )
        if not instrument:
            raise ValueError(f"Instrument not found: {data['symbol']}")

        strategy = StrategyRepository.get_by_id(data["strategy_id"])
        if not strategy:
            raise ValueError(f"Strategy not found: {data['strategy_id']}")

        run = BacktestRun.objects.create(
            user=user,
            strategy=strategy,
            instrument=instrument,
            timeframe=data["timeframe"],
            from_date=data["from_date"],
            to_date=data["to_date"],
            initial_capital=data.get("initial_capital", 100000),
            position_size_pct=data.get("position_size_pct", 10),
            brokerage_per_trade=data.get("brokerage_per_trade", 20),
        )

        return run

    @staticmethod
    def execute(run: BacktestRun) -> dict:
        """
        Execute a backtest run.

        Returns result summary dict.
        """
        logger.info(
            f"BacktestService: starting run {run.id} — "
            f"{run.strategy.name} | {run.instrument.symbol}"
        )

        run.status = "RUNNING"
        run.started_at = timezone.now()
        run.save()

        start_time = time.time()

        try:
            # Run engine
            engine = BacktestEngine(run)
            trade_dicts = engine.run_backtest()

            # Persist trades
            trade_objects = []
            for trade_dict in trade_dicts:
                trade = BacktestTrade(run=run, **trade_dict)
                trade_objects.append(trade)

            BacktestTrade.objects.bulk_create(trade_objects, batch_size=500)

            # Generate report
            saved_trades = list(BacktestTradeRepository.get_by_run(run))
            result = ReportService.generate(
                run=run,
                trades=saved_trades,
                equity_curve=engine.equity_curve,
            )

            # Update run
            duration = time.time() - start_time
            run.status = "COMPLETE"
            run.completed_at = timezone.now()
            run.duration_seconds = round(duration, 2)
            run.candles_processed = engine.candles_processed
            run.save()

            logger.info(
                f"BacktestService: run {run.id} complete — "
                f"{result.total_trades} trades | "
                f"WR: {result.win_rate}% | "
                f"Return: {result.total_return_pct}%"
            )

            return {
                "run_id": run.id,
                "status": "COMPLETE",
                "total_trades": result.total_trades,
                "win_rate": float(result.win_rate),
                "total_return_pct": float(result.total_return_pct),
                "total_net_pnl": float(result.total_net_pnl),
                "max_drawdown_pct": float(result.max_drawdown_pct),
                "sharpe_ratio": float(result.sharpe_ratio),
                "duration_seconds": duration,
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"BacktestService run {run.id} failed: {e}")

            run.status = "FAILED"
            run.completed_at = timezone.now()
            run.duration_seconds = round(duration, 2)
            run.error_message = str(e)
            run.save()

            return {
                "run_id": run.id,
                "status": "FAILED",
                "error": str(e),
            }

    @staticmethod
    def get_runs(user, limit: int = 20):
        """Return recent backtest runs for a user."""
        return BacktestRunRepository.get_by_user(user, limit)

    @staticmethod
    def get_run(user, run_id: int):
        """Return a single run."""
        return BacktestRunRepository.get_by_id_for_user(user, run_id)

    @staticmethod
    def get_trades(run: BacktestRun):
        """Return trades for a run."""
        return BacktestTradeRepository.get_by_run(run)