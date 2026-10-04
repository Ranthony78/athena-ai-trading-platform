from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from .api.views import MarketEngineStatusAPIView
from .engine.market_state import IST, MarketState
from .providers.provider_factory import ProviderFactory
from .providers.zerodha_provider import ZerodhaProvider
from .services.option_chain_service import OptionChainService


class MarketDataRegressionTests(SimpleTestCase):
    @override_settings(MARKET_PROVIDER="zerodha")
    def test_status_reports_open_and_closed_sessions(self):
        for hour, expected in [(10, True), (18, False)]:
            with (
                self.subTest(hour=hour),
                patch.object(
                    MarketState,
                    "now_ist",
                    return_value=datetime(2026, 9, 28, hour, tzinfo=IST),
                ),
            ):
                request = APIRequestFactory().get("/api/market/engine/status/")
                force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
                response = MarketEngineStatusAPIView.as_view()(request)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["data"]["is_live"], expected)
                self.assertEqual(response.data["data"]["provider"], "zerodha")

    @override_settings(MARKET_PROVIDER="invalid")
    def test_invalid_provider_does_not_silently_return_mock_data(self):
        with self.assertRaises(ImproperlyConfigured):
            ProviderFactory.get_provider()

    @override_settings(MARKET_PROVIDER="mock")
    def test_mock_chain_explains_empty_result_without_catalog_access(self):
        service = OptionChainService()
        self.assertEqual(service.get_chain("NIFTY"), [])
        self.assertIn("mock provider", service.status_message)

    @override_settings(MARKET_PROVIDER="zerodha")
    @patch.object(OptionChainService, "_get_available_expiries", return_value=[])
    def test_missing_catalog_does_not_call_broker(self, expiries):
        with patch(
            "apps.market_data.services.market_service.MarketService.quote"
        ) as quote:
            service = OptionChainService()
            self.assertEqual(service.get_chain("NIFTY"), [])
            self.assertIn("NFO contracts", service.status_message)
            quote.assert_not_called()

    @override_settings(MARKET_PROVIDER="zerodha")
    @patch.object(
        OptionChainService, "_get_available_expiries", return_value=[date(2026, 9, 29)]
    )
    def test_unavailable_option_quotes_are_distinguished_from_catalog(self, expiries):
        with (
            patch(
                "apps.market_data.services.market_service.MarketService.quote",
                return_value={"ltp": 25000},
            ),
            patch(
                "apps.market_data.services.market_service.MarketService.option_chain",
                return_value=[],
            ),
        ):
            service = OptionChainService()
            self.assertEqual(service.get_chain("NIFTY"), [])
            self.assertIn("contracts exist", service.status_message)

    def test_quotes_cover_more_than_200_contracts_and_skip_missing_quotes(self):
        options = [
            SimpleNamespace(
                exchange="NFO",
                trading_symbol=f"TEST{i}",
                strike=i,
                option_type="CE",
                expiry=date(2026, 9, 29),
                lot_size=75,
            )
            for i in range(208)
        ]
        provider = ZerodhaProvider()
        with (
            patch(
                "apps.market_data.repositories.instrument_repository.InstrumentRepository.get_options",
                return_value=options,
            ),
            patch.object(provider, "_get_service") as get_service,
        ):
            service = get_service.return_value
            service.get_quotes.side_effect = lambda symbols: {
                symbol: {"last_price": 10}
                for symbol in symbols
                if symbol != "NFO:TEST0"
            }
            chain = provider.get_option_chain("NIFTY", expiry="2026-09-29")
            self.assertEqual(len(chain), 207)
            self.assertEqual(
                [len(call.args[0]) for call in service.get_quotes.call_args_list],
                [200, 8],
            )
            self.assertEqual(chain[-1]["trading_symbol"], "TEST207")
            self.assertEqual(chain[-1]["lot_size"], 75)

    def test_development_disables_orders(self):
        from config.settings import development

        self.assertFalse(development.LIVE_TRADING_ENABLED)

    def test_disabled_order_endpoint_never_calls_broker(self):
        # The permission rules themselves are tested in
        # apps.zerodha.test_live_trading; here a denial must stop the request
        # before any broker object is created.
        from apps.zerodha.api.views import ZerodhaOrderListAPIView

        request = APIRequestFactory().post("/api/zerodha/orders/", {}, format="json")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
        with (
            patch(
                "apps.zerodha.api.views.LiveTradingService.can_place",
                return_value=(False, "blocked"),
            ),
            patch("apps.zerodha.api.views.KiteService") as broker,
        ):
            response = ZerodhaOrderListAPIView.as_view()(request)
            self.assertEqual(response.status_code, 403)
            broker.assert_not_called()
