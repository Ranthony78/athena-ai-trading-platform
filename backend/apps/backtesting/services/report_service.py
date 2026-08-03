import logging
from decimal import Decimal

import numpy as np

from ..models import BacktestResult, BacktestRun, BacktestTrade

logger = logging.getLogger(__name__)


class ReportService:
    """
    Calculates comprehensive backtest statistics from trade data.
    Generates BacktestResult from completed BacktestRun.
    """

    @staticmethod
    def generate(
        run: BacktestRun,
        trades: list[BacktestTrade],
        equity_curve: list[dict],
    ) -> BacktestResult:
        """
        Generate a BacktestResult from trade records.

        Args:
            run:          The BacktestRun instance
            trades:       List of BacktestTrade instances
            equity_curve: List of {time, capital} dicts

        Returns:
            BacktestResult instance
        """
        if not trades:
            return BacktestResult.objects.create(
                run=run,
                total_trades=0,
                initial_capital=run.initial_capital,
                final_capital=run.initial_capital,
                equity_curve=equity_curve,
            )

        pnls = [float(t.net_pnl) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_trades = len(trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = round(winning_trades / total_trades * 100, 2)

        total_pnl = sum(float(t.pnl) for t in trades)
        total_net_pnl = sum(pnls)
        avg_pnl = round(total_net_pnl / total_trades, 2)
        avg_win = round(sum(wins) / len(wins), 2) if wins else 0
        avg_loss = round(sum(losses) / len(losses), 2) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0

        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = round(
            gross_profit / gross_loss, 2
        ) if gross_loss > 0 else 0

        # Capital
        final_capital = float(trades[-1].capital_after) if trades else float(run.initial_capital)
        total_return_pct = round(
            (final_capital - float(run.initial_capital)) / float(run.initial_capital) * 100, 2
        )

        # Max drawdown
        max_drawdown, max_drawdown_pct = ReportService._calculate_drawdown(
            equity_curve=equity_curve,
            initial_capital=float(run.initial_capital),
        )

        # Sharpe ratio
        sharpe = ReportService._calculate_sharpe(pnls)

        # Expectancy
        expectancy = round(
            (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss), 2
        )

        # Risk/reward
        risk_reward = round(
            abs(avg_win / avg_loss), 2
        ) if avg_loss != 0 else 0

        # Consecutive wins/losses
        max_consec_wins, max_consec_losses = ReportService._consecutive_stats(pnls)

        return BacktestResult.objects.create(
            run=run,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=Decimal(str(win_rate)),
            total_pnl=Decimal(str(round(total_pnl, 2))),
            total_net_pnl=Decimal(str(round(total_net_pnl, 2))),
            avg_pnl_per_trade=Decimal(str(avg_pnl)),
            avg_win=Decimal(str(avg_win)),
            avg_loss=Decimal(str(avg_loss)),
            largest_win=Decimal(str(largest_win)),
            largest_loss=Decimal(str(largest_loss)),
            profit_factor=Decimal(str(profit_factor)),
            initial_capital=run.initial_capital,
            final_capital=Decimal(str(round(final_capital, 2))),
            total_return_pct=Decimal(str(total_return_pct)),
            max_drawdown=Decimal(str(round(max_drawdown, 2))),
            max_drawdown_pct=Decimal(str(round(max_drawdown_pct, 2))),
            sharpe_ratio=Decimal(str(round(sharpe, 4))),
            expectancy=Decimal(str(expectancy)),
            risk_reward_ratio=Decimal(str(risk_reward)),
            consecutive_wins=max_consec_wins,
            consecutive_losses=max_consec_losses,
            equity_curve=equity_curve,
        )

    @staticmethod
    def _calculate_drawdown(
        equity_curve: list[dict],
        initial_capital: float,
    ) -> tuple[float, float]:
        """Calculate maximum drawdown and drawdown percentage."""
        if not equity_curve:
            return 0.0, 0.0

        capitals = [e["capital"] for e in equity_curve]
        peak = initial_capital
        max_dd = 0.0
        max_dd_pct = 0.0

        for capital in capitals:
            if capital > peak:
                peak = capital
            dd = peak - capital
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        return max_dd, max_dd_pct

    @staticmethod
    def _calculate_sharpe(
        pnls: list[float],
        risk_free_rate: float = 0.06,
    ) -> float:
        """
        Calculate Sharpe ratio.
        Uses daily risk-free rate assuming 252 trading days.
        """
        if len(pnls) < 2:
            return 0.0

        pnl_array = np.array(pnls)
        daily_rf = risk_free_rate / 252
        excess_returns = pnl_array - daily_rf

        std = np.std(excess_returns)
        if std == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / std * np.sqrt(252)
        return float(round(sharpe, 4))

    @staticmethod
    def _consecutive_stats(pnls: list[float]) -> tuple[int, int]:
        """Calculate max consecutive wins and losses."""
        max_wins = max_losses = 0
        cur_wins = cur_losses = 0

        for pnl in pnls:
            if pnl > 0:
                cur_wins += 1
                cur_losses = 0
            else:
                cur_losses += 1
                cur_wins = 0

            max_wins = max(max_wins, cur_wins)
            max_losses = max(max_losses, cur_losses)

        return max_wins, max_losses