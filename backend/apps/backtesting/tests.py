"""
Tests for backtest statistics calculations (ReportService.generate()).

Covers win rate, avg win/loss, profit factor, expectancy, risk/reward,
consecutive win/loss streaks, max drawdown, and Sharpe ratio — the
numbers a person would actually trust to judge whether a strategy is
worth running with real (or paper) money.

Two things worth your attention, documented below rather than silently
"fixed", since both are judgment calls about methodology/semantics
rather than crashes:

1. NAMING: profit_factor's internal variables are named `gross_profit`/
   `gross_loss`, but they're actually summed from `net_pnl` (post-
   brokerage), not gross pnl. The ratio itself is still a meaningful
   "money made per money lost" figure — just be aware it's net-based
   despite the variable names. See test_profit_factor.

2. METHODOLOGY: _calculate_sharpe() subtracts a fractional daily
   risk-free rate (~0.0002) from raw per-trade PnL values measured in
   rupees (often hundreds/thousands), then annualizes with sqrt(252)
   as if each trade were one trading day. This doesn't correspond to
   a standard Sharpe ratio (which is normally computed on percentage
   returns, not absolute currency PnL, and on a real time axis, not
   one point per trade). The number is internally consistent and
   deterministic, but shouldn't be read as "Sharpe ratio" in the
   conventional sense when comparing to other systems. See
   test_sharpe_ratio_current_formula.

3. MINOR: BacktestRun.initial_capital uses a raw float literal as its
   model default (default=100000.00 instead of Decimal("100000.00")) —
   the same pattern that caused a real crash in PaperAccount.balance.
   It happens to be safe here because every usage wraps it in float()
   first, but it's the same fragile pattern and worth tidying up
   preventively.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.market_data.models import Instrument
from apps.strategies.models import Strategy
from apps.backtesting.models import BacktestRun, BacktestTrade
from apps.backtesting.services.report_service import ReportService

User = get_user_model()


class ReportServiceTestCase(TestCase):
    """Tests for ReportService.generate() and its helper calculations."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="backtester", password="testpass123"
        )
        self.instrument = Instrument.objects.create(
            instrument_token=999002,
            exchange_token=999002,
            exchange="NSE",
            symbol="NIFTY",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )
        self.strategy = Strategy.objects.create(
            name="Test Strategy",
            strategy_type="EMA_CROSSOVER",
            timeframe="15m",
        )
        self.run = BacktestRun.objects.create(
            user=self.user,
            strategy=self.strategy,
            instrument=self.instrument,
            timeframe="15m",
            from_date=date(2026, 1, 1),
            to_date=date(2026, 1, 31),
            initial_capital=Decimal("100000.00"),
        )

    def _make_trade(self, pnl: float, net_pnl: float) -> BacktestTrade:
        """Build a minimal, valid BacktestTrade for statistics testing."""
        return BacktestTrade.objects.create(
            run=self.run,
            direction="LONG",
            quantity=1,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("100.00"),
            entry_time=datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc),
            exit_time=datetime(2026, 1, 5, 11, 0, tzinfo=timezone.utc),
            pnl=Decimal(str(pnl)),
            pnl_pct=Decimal("0.0"),
            brokerage=Decimal("20.00"),
            net_pnl=Decimal(str(net_pnl)),
            signal="BUY",
            capital_after=Decimal("100000.00"),
        )

    # ------------------------------------------------------------------
    # Core statistics — using a fixed 5-trade set with known values
    # ------------------------------------------------------------------
    #
    # gross pnl: [120, -30, 220, -10, 0]   (sum = 300)
    # net pnl:   [100, -50, 200, -30, -20] (sum = 200)
    # wins (net > 0):  [100, 200]
    # losses (net <=0): [-50, -30, -20]

    def _make_standard_trade_set(self):
        gross = [120.0, -30.0, 220.0, -10.0, 0.0]
        net = [100.0, -50.0, 200.0, -30.0, -20.0]
        return [
            self._make_trade(pnl=g, net_pnl=n) for g, n in zip(gross, net)
        ]

    def test_win_loss_counts_and_win_rate(self):
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.total_trades, 5)
        self.assertEqual(result.winning_trades, 2)
        self.assertEqual(result.losing_trades, 3)
        self.assertEqual(result.win_rate, Decimal("40.00"))

    def test_total_pnl_is_gross_total_net_pnl_is_net(self):
        """total_pnl sums gross `pnl`; total_net_pnl sums `net_pnl` —
        these are two different, correctly-separated numbers."""
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.total_pnl, Decimal("300.00"))
        self.assertEqual(result.total_net_pnl, Decimal("200.00"))

    def test_avg_win_avg_loss_and_extremes(self):
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.avg_pnl_per_trade, Decimal("40.00"))
        self.assertEqual(result.avg_win, Decimal("150.00"))
        self.assertEqual(result.avg_loss, Decimal("-33.33"))
        self.assertEqual(result.largest_win, Decimal("200.00"))
        self.assertEqual(result.largest_loss, Decimal("-50.00"))

    def test_profit_factor(self):
        """
        NOTE: despite the internal variable names gross_profit/
        gross_loss, this is computed from net_pnl values, not gross
        pnl. 300(gross wins net-basis) / 100... see docstring at top
        of this file. Value pinned here matches the actual algorithm.
        """
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        # sum(wins)=300, abs(sum(losses))=100 → 300/100 = 3.0
        self.assertEqual(result.profit_factor, Decimal("3.00"))

    def test_expectancy(self):
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        # (0.40 * 150.00) + (0.60 * -33.33) = 60.00 - 19.998 = 40.002 → 40.00
        self.assertEqual(result.expectancy, Decimal("40.00"))

    def test_risk_reward_ratio(self):
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        # abs(150.00 / -33.33) = 4.5005... → 4.50
        self.assertEqual(result.risk_reward_ratio, Decimal("4.50"))

    def test_consecutive_wins_and_losses(self):
        """Trade order: W, L, W, L, L → max streak of 1 win, 2 losses."""
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.consecutive_wins, 1)
        self.assertEqual(result.consecutive_losses, 2)

    def test_final_capital_and_return_pct(self):
        trades = self._make_standard_trade_set()
        # capital_after on the last trade drives final_capital
        trades[-1].capital_after = Decimal("100200.00")
        trades[-1].save()

        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.final_capital, Decimal("100200.00"))
        # (100200 - 100000) / 100000 * 100 = 0.20%
        self.assertEqual(result.total_return_pct, Decimal("0.20"))

    # ------------------------------------------------------------------
    # Max drawdown — dedicated equity curve
    # ------------------------------------------------------------------

    def test_max_drawdown(self):
        """
        Equity curve: 100000 → 105000 → 95000 → 110000 → 90000 → 120000
        Peak tracks the running high; drawdown is peak minus current.
        The worst drawdown occurs at the 90000 point, after a peak of
        110000: dd = 20000, dd_pct = 20000/110000*100 = 18.18%.
        """
        equity_curve = [
            {"time": "t1", "capital": 100000},
            {"time": "t2", "capital": 105000},
            {"time": "t3", "capital": 95000},
            {"time": "t4", "capital": 110000},
            {"time": "t5", "capital": 90000},
            {"time": "t6", "capital": 120000},
        ]
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve)

        self.assertEqual(result.max_drawdown, Decimal("20000.00"))
        self.assertEqual(result.max_drawdown_pct, Decimal("18.18"))

    def test_max_drawdown_empty_curve_is_zero(self):
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.max_drawdown, Decimal("0.00"))
        self.assertEqual(result.max_drawdown_pct, Decimal("0.00"))

    # ------------------------------------------------------------------
    # Sharpe ratio — documents the current formula's exact behavior
    # ------------------------------------------------------------------

    def test_sharpe_ratio_current_formula(self):
        """
        Pins the exact output of the current Sharpe calculation for
        the standard 5-trade net-pnl set [100, -50, 200, -30, -20].
        See the METHODOLOGY note at the top of this file — this value
        is deterministic and internally consistent, but the formula
        mixes absolute currency PnL with a fractional risk-free rate
        and treats each trade as one trading day, so it should not be
        compared to a conventional Sharpe ratio computed on returns.
        """
        trades = self._make_standard_trade_set()
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.sharpe_ratio, Decimal("6.6345"))

    def test_sharpe_ratio_with_fewer_than_two_trades_is_zero(self):
        trades = [self._make_trade(pnl=100.0, net_pnl=100.0)]
        result = ReportService.generate(self.run, trades, equity_curve=[])

        self.assertEqual(result.sharpe_ratio, Decimal("0.0000"))

    # ------------------------------------------------------------------
    # Empty trades edge case
    # ------------------------------------------------------------------

    def test_generate_with_no_trades_does_not_crash(self):
        """With zero trades, generate() should return a valid
        BacktestResult with everything at its default/zero state,
        not raise an exception."""
        result = ReportService.generate(self.run, trades=[], equity_curve=[])

        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.initial_capital, self.run.initial_capital)
        self.assertEqual(result.final_capital, self.run.initial_capital)
        self.assertEqual(result.win_rate, Decimal("0.00"))
        self.assertEqual(result.sharpe_ratio, Decimal("0.0000"))
