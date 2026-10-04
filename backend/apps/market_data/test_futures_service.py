from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from .models import Instrument
from .services.futures_service import FuturesService

TODAY = date(2026, 10, 4)


def make_future(token, expiry, symbol="NIFTY", exchange="NFO", active=True):
    return Instrument.objects.create(
        instrument_token=token,
        exchange=exchange,
        symbol=symbol,
        trading_symbol=f"{symbol}{token}FUT",
        instrument_type="FUT",
        expiry=expiry,
        is_active=active,
    )


@patch("django.utils.timezone.localdate", return_value=TODAY)
class FrontContractTests(TestCase):

    def test_picks_nearest_unexpired_active_contract(self, _):
        make_future(1, date(2026, 10, 1))  # expired
        near = make_future(2, date(2026, 10, 29))
        make_future(3, date(2026, 11, 26))
        make_future(4, date(2026, 10, 15), active=False)
        make_future(5, date(2026, 10, 10), symbol="BANKNIFTY")

        self.assertEqual(FuturesService.front_contract("NIFTY"), near)

    def test_none_when_no_contract(self, _):
        self.assertIsNone(FuturesService.front_contract("NIFTY"))


@patch("django.utils.timezone.localdate", return_value=TODAY)
class SnapshotTests(TestCase):

    def setUp(self):
        self.contract = make_future(2, date(2026, 10, 29))

    def snapshot(self, quote, **kwargs):
        fake = SimpleNamespace(quote=lambda symbol: quote)
        with patch(
            "apps.market_data.services.market_service.MarketService",
            return_value=fake,
        ):
            return FuturesService.snapshot("NIFTY", kwargs.get("user", object()))

    @override_settings(MARKET_PROVIDER="zerodha")
    def test_returns_vwap_volume_and_oi(self, _):
        result = self.snapshot(
            {
                "ltp": 24100.5,
                "average_price": 24050.0,
                "volume": 1000,
                "oi": 5000,
                "high": 24200,
                "low": 23900,
                "close": 24000,
            }
        )
        self.assertEqual(result["contract"], self.contract.trading_symbol)
        self.assertEqual(result["vwap"], 24050.0)
        self.assertEqual(result["oi"], 5000)

    @override_settings(MARKET_PROVIDER="zerodha")
    def test_unusable_quote_is_none(self, _):
        self.assertIsNone(self.snapshot({"ltp": 0}))
        self.assertIsNone(self.snapshot(None))

    @override_settings(MARKET_PROVIDER="zerodha")
    def test_missing_vwap_is_none_not_zero(self, _):
        self.assertIsNone(self.snapshot({"ltp": 100, "average_price": 0})["vwap"])

    @override_settings(MARKET_PROVIDER="mock")
    def test_mock_provider_is_never_used(self, _):
        self.assertIsNone(self.snapshot({"ltp": 100}))

    @override_settings(MARKET_PROVIDER="zerodha")
    def test_no_user_is_none(self, _):
        self.assertIsNone(self.snapshot({"ltp": 100}, user=None))
