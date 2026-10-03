"""
Regression: "today's orders / trades" must use the local (Asia/Kolkata) date.

order_time__date and exit_time__date are evaluated by the database in the
local timezone, but "today" was taken from the UTC date, so between 00:00 and
05:30 IST the paper-trading "today" screens looked at yesterday.
"""

from datetime import datetime
from datetime import timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.market_data.models import Instrument
from apps.paper_trading.models import PaperAccount, PaperOrder, PaperTrade
from apps.paper_trading.repositories.paper_repository import (
    PaperOrderRepository,
    PaperTradeRepository,
)

User = get_user_model()

# 2026-10-03 20:30 UTC is 2026-10-04 02:00 IST.
NIGHT = datetime(2026, 10, 3, 20, 30, tzinfo=dt_timezone.utc)
EARLIER = datetime(2026, 10, 3, 9, 30, tzinfo=dt_timezone.utc)  # 15:00 IST on the 3rd


@patch("django.utils.timezone.now", return_value=NIGHT)
class PaperTradingLocalDateTests(TestCase):

    def setUp(self):
        user = User.objects.create_user("pt", "pt@example.com", "pw-Pt-123456")
        self.account = PaperAccount.objects.create(user=user)
        self.instrument = Instrument.objects.create(
            instrument_token=888000001,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )

    def make_order(self, at):
        order = PaperOrder.objects.create(
            account=self.account,
            instrument=self.instrument,
            transaction_type="BUY",
            quantity=1,
        )
        PaperOrder.objects.filter(pk=order.pk).update(order_time=at)  # auto_now_add
        return order

    def make_trade(self, at):
        return PaperTrade.objects.create(
            account=self.account,
            instrument=self.instrument,
            direction="LONG",
            quantity=1,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("101.00"),
            entry_time=at,
            exit_time=at,
            pnl=Decimal("1.00"),
        )

    def test_orders_placed_after_local_midnight_count_as_today(self, _now):
        today = self.make_order(NIGHT)
        self.make_order(EARLIER)  # the previous local day

        found = list(PaperOrderRepository.get_today(self.account))

        self.assertEqual([o.pk for o in found], [today.pk])

    def test_trades_closed_after_local_midnight_count_as_today(self, _now):
        today = self.make_trade(NIGHT)
        self.make_trade(EARLIER)

        found = list(PaperTradeRepository.get_today(self.account))

        self.assertEqual([t.pk for t in found], [today.pk])
