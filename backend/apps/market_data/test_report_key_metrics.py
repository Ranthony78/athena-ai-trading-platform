from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.analysis_report_service import AnalysisReportService

FUTURES = "apps.market_data.services.futures_service.FuturesService.snapshot"
BREADTH = (
    "apps.market_data.services.market_breadth_service.MarketBreadthService.get_breadth"
)
MARKET = "apps.market_data.services.market_service.MarketService"


def market_with(quotes):
    return SimpleNamespace(quote=lambda symbol: quotes.get(symbol))


class KeyMetricsTests(SimpleTestCase):

    def test_assembles_futures_vix_gap_and_breadth(self):
        quotes = {
            "VIX": {"ltp": 12.0, "close": 10.0, "high": 12.5},
            "BANKNIFTY": {"ltp": 101, "open": 102, "close": 100},
        }
        with (
            patch(FUTURES, return_value={"vwap": 54839.8}),
            patch(BREADTH, return_value={"advances": 7}),
            patch(MARKET, return_value=market_with(quotes)),
        ):
            result = AnalysisReportService._get_key_metrics("BANKNIFTY", object())

        self.assertEqual(result["futures"], {"vwap": 54839.8})
        self.assertEqual(result["vix"]["change_pct"], 20.0)
        self.assertEqual(result["gap"]["retrace_pct"], 50.0)
        self.assertEqual(result["breadth"], {"advances": 7})

    def test_each_part_degrades_alone(self):
        with (
            patch(FUTURES, side_effect=RuntimeError("down")),
            patch(BREADTH, return_value=None),
            patch(MARKET, return_value=market_with({})),
        ):
            result = AnalysisReportService._get_key_metrics("BANKNIFTY", object())

        self.assertEqual(
            result, {"futures": None, "vix": None, "gap": None, "breadth": None}
        )

    def test_no_user_gives_no_quote_based_metrics(self):
        with patch(FUTURES, return_value=None), patch(BREADTH, return_value=None):
            result = AnalysisReportService._get_key_metrics("BANKNIFTY", None)

        self.assertIsNone(result["vix"])
        self.assertIsNone(result["gap"])
