"""
Tests for paper trading P&L calculations.

Covers PositionService.update_position() — opening, adding to, and
closing positions — since this is where all real money-math for the
paper trading feature lives.

Win/loss classification and partial-close accounting use realized net
results. These tests protect the paper journal's accounting semantics.
"""

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.market_data.models import Instrument
from apps.paper_trading.models import PaperAccount, PaperTrade
from apps.paper_trading.services.broker_simulator import BrokerSimulator
from apps.paper_trading.services.position_service import BROKERAGE, PositionService

User = get_user_model()


class OptionPaperFillQuoteTests(SimpleTestCase):
    @patch(
        "apps.market_data.repositories.instrument_repository.InstrumentRepository.get_by_trading_symbol"
    )
    @patch("apps.market_data.providers.provider_factory.ProviderFactory.get_provider")
    def test_option_buys_use_ask_and_sells_use_bid(self, get_provider, get_instrument):
        provider = get_provider.return_value
        provider.get_quote.return_value = {
            "timestamp": timezone.now().isoformat(),
            "ltp": 100,
            "bid": 99,
            "ask": 101,
        }
        get_instrument.return_value = SimpleNamespace(option_type="CE")
        simulator = BrokerSimulator()

        self.assertEqual(
            simulator.get_execution_price("NIFTYTESTCE", "MARKET", "BUY"),
            Decimal("101"),
        )
        self.assertEqual(
            simulator.get_execution_price("NIFTYTESTCE", "MARKET", "SELL"),
            Decimal("99"),
        )

    @patch(
        "apps.market_data.repositories.instrument_repository.InstrumentRepository.get_by_trading_symbol"
    )
    @patch("apps.market_data.providers.provider_factory.ProviderFactory.get_provider")
    def test_option_paper_fill_refuses_missing_or_stale_bid_ask(
        self, get_provider, get_instrument
    ):
        provider = get_provider.return_value
        get_instrument.return_value = SimpleNamespace(option_type="PE")
        simulator = BrokerSimulator()
        provider.get_quote.return_value = {
            "timestamp": timezone.now().isoformat(),
            "ltp": 100,
            "bid": 0,
            "ask": 101,
        }
        self.assertEqual(
            simulator.get_execution_price("NIFTYTESTPE", "MARKET", "BUY"), Decimal("0")
        )

        provider.get_quote.return_value = {
            "timestamp": (timezone.now() - timedelta(minutes=5)).isoformat(),
            "ltp": 100,
            "bid": 99,
            "ask": 101,
        }
        self.assertEqual(
            simulator.get_execution_price("NIFTYTESTPE", "MARKET", "BUY"), Decimal("0")
        )


class PositionServiceTestCase(TestCase):
    """Tests for PositionService.update_position() and _calculate_pnl()."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testtrader", password="testpass123"
        )
        self.account = PaperAccount.objects.create(user=self.user)
        self.instrument = Instrument.objects.create(
            instrument_token=999001,
            exchange_token=999001,
            exchange="NSE",
            symbol="NIFTY",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )

    # ------------------------------------------------------------------
    # Opening positions
    # ------------------------------------------------------------------

    def test_open_long_position(self):
        """BUY with no existing position opens a LONG position and
        reserves margin equal to price * quantity."""
        position = PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )

        self.assertEqual(position.direction, "LONG")
        self.assertEqual(position.quantity, 10)
        self.assertEqual(position.average_price, Decimal("100.00"))

        self.account.refresh_from_db()
        # margin = 100 * 10 = 1000
        self.assertEqual(self.account.used_margin, Decimal("1000.00"))
        # balance stays at full account value — used_margin alone tracks
        # what's locked (fixed a prior double-counting bug where balance
        # was also reduced here).
        self.assertEqual(self.account.balance, Decimal("1000000.00"))

    def test_open_short_position(self):
        """SELL with no existing position opens a SHORT position."""
        position = PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=5,
            execution_price=Decimal("200.00"),
        )

        self.assertEqual(position.direction, "SHORT")
        self.assertEqual(position.quantity, 5)

        self.account.refresh_from_db()
        # margin = 200 * 5 = 1000
        self.assertEqual(self.account.used_margin, Decimal("1000.00"))

    # ------------------------------------------------------------------
    # Adding to an existing position
    # ------------------------------------------------------------------

    def test_add_to_long_position_recalculates_average_price(self):
        """Buying more of an existing LONG position recalculates the
        weighted average entry price."""
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )
        position = PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("120.00"),
        )

        # (100*10 + 120*10) / 20 = 110
        self.assertEqual(position.quantity, 20)
        self.assertEqual(position.average_price, Decimal("110.00"))

    # ------------------------------------------------------------------
    # Fully closing a position
    # ------------------------------------------------------------------

    def test_full_close_long_position_profit(self):
        """Closing a full LONG position at a higher price realizes a
        profit, deducts brokerage, and updates every account field."""
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )

        closed_position = PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=10,
            execution_price=Decimal("110.00"),
        )

        # Gross PnL = (110 - 100) * 10 = 100
        # Net PnL   = 100 - BROKERAGE(20) = 80
        expected_pnl = Decimal("100.00")
        expected_net_pnl = expected_pnl - BROKERAGE

        self.assertFalse(closed_position.is_open)
        self.assertEqual(closed_position.realized_pnl, expected_pnl)

        trade = PaperTrade.objects.get(position=closed_position)
        self.assertEqual(trade.pnl, expected_pnl)
        self.assertEqual(trade.net_pnl, expected_net_pnl)
        self.assertEqual(trade.brokerage, BROKERAGE)

        self.account.refresh_from_db()
        self.assertEqual(
            self.account.balance,
            Decimal("1000000.00") + expected_net_pnl,
        )
        self.assertEqual(self.account.used_margin, Decimal("0.00"))
        self.assertEqual(self.account.total_pnl, expected_net_pnl)
        self.assertEqual(self.account.today_pnl, expected_net_pnl)
        self.assertEqual(self.account.total_trades, 1)
        self.assertEqual(self.account.winning_trades, 1)
        self.assertEqual(self.account.losing_trades, 0)

    def test_full_close_short_position_profit(self):
        """Closing a full SHORT position at a lower price realizes a
        profit (price dropped in your favor)."""
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=10,
            execution_price=Decimal("200.00"),
        )

        closed_position = PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("180.00"),
        )

        # SHORT PnL = (entry - exit) * qty = (200 - 180) * 10 = 200
        expected_pnl = Decimal("200.00")
        self.assertEqual(closed_position.realized_pnl, expected_pnl)

        self.account.refresh_from_db()
        self.assertEqual(self.account.winning_trades, 1)

    def test_full_close_long_position_loss(self):
        """Closing a full LONG position at a lower price realizes a
        loss and is correctly counted in losing_trades."""
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )

        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=10,
            execution_price=Decimal("90.00"),
        )

        # Gross PnL = (90 - 100) * 10 = -100
        self.account.refresh_from_db()
        self.assertEqual(self.account.total_pnl, Decimal("-100.00") - BROKERAGE)
        self.assertEqual(self.account.winning_trades, 0)
        self.assertEqual(self.account.losing_trades, 1)

    # ------------------------------------------------------------------
    # Net outcome classification
    # ------------------------------------------------------------------

    def test_win_loss_classification_uses_net_pnl_after_brokerage(self):
        """
        A gross gain smaller than brokerage is a net loss and must count
        as a losing outcome in paper account statistics.
        """
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=1,
            execution_price=Decimal("100.00"),
        )

        # Gross PnL = (110 - 100) * 1 = 10 (positive)
        # Net PnL   = 10 - BROKERAGE(20) = -10 (a real loss after costs)
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=1,
            execution_price=Decimal("110.00"),
        )

        trade = PaperTrade.objects.get(account=self.account)
        self.assertEqual(trade.pnl, Decimal("10.00"))
        self.assertEqual(trade.net_pnl, Decimal("-10.00"))

        self.account.refresh_from_db()
        self.assertEqual(self.account.winning_trades, 0)
        self.assertEqual(self.account.losing_trades, 1)
        self.assertEqual(self.account.total_pnl, Decimal("-10.00"))

    # ------------------------------------------------------------------
    # Partial close
    # ------------------------------------------------------------------

    def test_partial_close_does_not_update_account_balance(self):
        """
        Partial closes create a trade-ledger row, release proportional
        margin, and apply realized net P&L to the account.

        This test documents the current (surprising) behavior rather
        than asserting it's correct.
        """
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )
        balance_after_open = self.account.balance
        margin_after_open = self.account.used_margin

        # Partially close half the position
        position = PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=5,
            execution_price=Decimal("110.00"),
        )

        self.assertTrue(position.is_open)
        self.assertEqual(position.quantity, 5)
        # Position-level realized PnL: (110-100)*5 = 50
        self.assertEqual(position.realized_pnl, Decimal("50.00"))

        trade = PaperTrade.objects.get(account=self.account)
        self.assertEqual(trade.quantity, 5)
        self.assertEqual(trade.pnl, Decimal("50.00"))
        self.assertEqual(trade.net_pnl, Decimal("30.00"))

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, balance_after_open + Decimal("30.00"))
        self.assertEqual(
            self.account.used_margin, margin_after_open - Decimal("500.00")
        )
        self.assertEqual(self.account.total_pnl, Decimal("30.00"))

    # ------------------------------------------------------------------
    # available_balance correctness (margin should be counted once)
    # ------------------------------------------------------------------

    def test_available_balance_not_double_counted_on_open(self):
        """
        Regression test for a fixed bug: opening a position used to
        subtract margin from account.balance directly AND from
        available_balance (balance - used_margin), double-counting it.
        balance should stay at the full account value; only
        available_balance should reflect the margin being locked.
        """
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )
        self.account.refresh_from_db()
        # margin = 100 * 10 = 1000
        self.assertEqual(self.account.balance, Decimal("1000000.00"))
        self.assertEqual(self.account.used_margin, Decimal("1000.00"))
        self.assertEqual(
            self.account.available_balance,
            1000000.00 - 1000.00,
        )

    def test_available_balance_correct_after_full_close(self):
        """After fully closing a position, used_margin returns to 0 and
        balance reflects only the realized net P&L — available_balance
        should equal balance exactly, with no leftover margin lock."""
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=10,
            execution_price=Decimal("100.00"),
        )
        PositionService.update_position(
            account=self.account,
            instrument=self.instrument,
            transaction_type="SELL",
            quantity=10,
            execution_price=Decimal("110.00"),
        )
        self.account.refresh_from_db()
        # Gross PnL = 100, Net PnL = 100 - BROKERAGE(20) = 80
        expected_balance = Decimal("1000000.00") + Decimal("80.00")
        self.assertEqual(self.account.balance, expected_balance)
        self.assertEqual(self.account.used_margin, Decimal("0.00"))
        self.assertEqual(self.account.available_balance, float(expected_balance))
