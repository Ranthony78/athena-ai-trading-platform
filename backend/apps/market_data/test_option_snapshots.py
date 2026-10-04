from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from . import tasks
from .models import Instrument, OptionSnapshot
from .services.option_snapshot_service import OptionSnapshotService

OPTION_CHAIN_SERVICE = (
    "apps.market_data.services.option_chain_service.OptionChainService"
)
MARKET_SERVICE = "apps.market_data.services.market_service.MarketService"
SESSION = "apps.market_data.engine.market_state.MarketState.session_info"
CONFIG_QS = "apps.zerodha.repositories.zerodha_repository.ZerodhaConfigRepository"
EXPIRY = date(2026, 10, 8)


def make_option(strike, option_type="CE"):
    return Instrument.objects.create(
        instrument_token=1000 + int(strike) + (1 if option_type == "PE" else 0),
        exchange="NFO",
        symbol="NIFTY",
        trading_symbol=f"NIFTY{int(strike)}{option_type}",
        instrument_type=option_type,
        option_type=option_type,
        strike=strike,
        expiry=EXPIRY,
    )


def chain_row(option, ltp=100, oi=500):
    return {
        "strike": float(option.strike),
        "option_type": option.option_type,
        "trading_symbol": option.trading_symbol,
        "expiry": str(EXPIRY),
        "ltp": ltp,
        "best_bid": ltp - 1,
        "best_ask": ltp + 1,
        "oi": oi,
        "volume": 10,
    }


class CaptureTests(TestCase):

    def capture(self, rows, spot=23000, **kwargs):
        chain = SimpleNamespace(
            get_chain_summary=lambda symbol: {
                "expiry": str(EXPIRY),
                "spot_price": spot,
            }
        )
        market = SimpleNamespace(option_chain=lambda symbol, expiry=None: rows)
        with (
            patch(OPTION_CHAIN_SERVICE, return_value=chain),
            patch(MARKET_SERVICE, return_value=market),
        ):
            return OptionSnapshotService.capture("NIFTY", object(), **kwargs)

    def test_stores_only_strikes_around_the_money(self):
        options = [make_option(s) for s in (22800, 22900, 23000, 23100, 23200)]
        rows = [chain_row(o) for o in options]

        saved = self.capture(rows, strikes_each_side=1)

        self.assertEqual(saved, 3)
        self.assertEqual(
            sorted(OptionSnapshot.objects.values_list("instrument__strike", flat=True)),
            [22900, 23000, 23100],
        )

    def test_skips_unpriced_and_unknown_contracts(self):
        priced = make_option(23000)
        unpriced = make_option(23100)
        rows = [
            chain_row(priced),
            chain_row(unpriced, ltp=0),
            {**chain_row(priced), "trading_symbol": "NOSUCH", "strike": 23000.0},
        ]

        self.assertEqual(self.capture(rows), 1)

    def test_raw_values_are_stored(self):
        option = make_option(23000, "PE")
        self.capture([chain_row(option, ltp=95.5, oi=1234)])

        snap = OptionSnapshot.objects.get()
        self.assertEqual((float(snap.ltp), snap.oi, snap.volume), (95.5, 1234, 10))
        self.assertEqual(float(snap.spot), 23000.0)
        self.assertEqual(float(snap.bid), 94.5)

    def test_no_usable_underlying_price_stores_nothing(self):
        option = make_option(23000)
        self.assertEqual(self.capture([chain_row(option)], spot=None), 0)
        self.assertEqual(OptionSnapshot.objects.count(), 0)


class PurgeTests(TestCase):

    def test_keeps_recent_and_drops_old(self):
        option = make_option(23000)
        for age in (1, 30):
            OptionSnapshot.objects.create(
                underlying="NIFTY",
                instrument=option,
                captured_at=timezone.now() - timedelta(days=age),
                spot=23000,
                ltp=100,
            )

        self.assertEqual(OptionSnapshotService.purge(days=20), 1)
        self.assertEqual(OptionSnapshot.objects.count(), 1)


class TaskGuardTests(TestCase):

    def test_skips_when_market_closed(self):
        with patch(SESSION, return_value={"is_live": False}):
            self.assertEqual(tasks.snapshot_option_chain(), "skipped (market closed)")

    def test_skips_without_a_valid_zerodha_token(self):
        with (
            patch(SESSION, return_value={"is_live": True}),
            patch(
                f"{CONFIG_QS}.model.objects.filter",
                return_value=SimpleNamespace(first=lambda: None),
            ),
        ):
            self.assertEqual(
                tasks.snapshot_option_chain(),
                "skipped (no valid Zerodha connection)",
            )
