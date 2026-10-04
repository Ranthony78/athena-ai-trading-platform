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


class OptionsBlockTests(SimpleTestCase):

    def test_options_block_adds_dte_matched_put_and_oi_walls(self):
        from datetime import date

        chain = [
            {
                "strike": 24100.0,
                "option_type": "CE",
                "ltp": 150.0,
                "oi": 900,
                "lot_size": 65,
            },
            {
                "strike": 24100.0,
                "option_type": "PE",
                "ltp": 120.0,
                "oi": 800,
                "lot_size": 65,
            },
            {
                "strike": 24200.0,
                "option_type": "CE",
                "ltp": 90.0,
                "oi": 1500,
                "lot_size": 65,
            },
            {
                "strike": 24000.0,
                "option_type": "PE",
                "ltp": 148.0,
                "oi": 2000,
                "lot_size": 65,
            },
        ]
        summary = {
            "atm_strike": 24100.0,
            "expiry": "2026-10-08",
            "spot_price": 24100.0,
            "pcr_oi": 1.2,
        }
        service = SimpleNamespace(
            get_chain_summary=lambda symbol: summary,
            get_chain=lambda symbol, expiry=None: chain,
        )
        with (
            patch(
                "apps.market_data.services.option_chain_service.OptionChainService",
                return_value=service,
            ),
            patch("django.utils.timezone.localdate", return_value=date(2026, 10, 5)),
        ):
            result = AnalysisReportService._get_options("NIFTY", object())

        self.assertEqual(result["dte"], 3)
        self.assertEqual(result["lot_size"], 65)
        self.assertEqual(result["matched_put"]["strike"], 24000.0)
        self.assertEqual(result["oi_walls"]["call_wall"]["strike"], 24200.0)
        self.assertEqual(result["oi_walls"]["put_wall"]["strike"], 24000.0)


HIST = "apps.market_data.services.historical_distribution_service.HistoricalDistributionService.close_direction_given_gap"


class GapAnalysisTests(SimpleTestCase):

    def run_gap(self, quote, stats=None, user=object()):
        with (
            patch(MARKET, return_value=market_with({"NIFTY": quote})),
            patch(HIST, return_value=stats),
        ):
            return AnalysisReportService._get_gap_analysis("NIFTY", user)

    def test_gap_down_continuation_is_the_down_close_share(self):
        stats = {"up_pct": 37.0, "down_pct": 55.0, "flat_pct": 8.0, "sample_size": 40}
        result = self.run_gap(
            {"close": 22620.45, "open": 22543.7, "ltp": 22421.95}, stats
        )

        self.assertEqual(result["gap"]["direction"], "DOWN")
        self.assertEqual(result["historical"]["continuation_pct"], 55.0)
        self.assertEqual(result["historical"]["reversal_pct"], 37.0)
        self.assertEqual(result["historical"]["gap_bucket"], "gap_down_mild")

    def test_gap_up_continuation_is_the_up_close_share(self):
        stats = {"up_pct": 60.0, "down_pct": 30.0, "flat_pct": 10.0, "sample_size": 25}
        result = self.run_gap({"close": 100, "open": 100.5, "ltp": 101}, stats)

        self.assertEqual(result["historical"]["continuation_pct"], 60.0)
        self.assertEqual(result["historical"]["reversal_pct"], 30.0)

    def test_thin_history_gives_no_base_rate(self):
        result = self.run_gap(
            {"close": 100, "open": 100.5, "ltp": 101}, {"error": "insufficient"}
        )
        self.assertFalse(result["historical"]["available"])
        self.assertIn("10", result["historical"]["reason"])

    def test_flat_open_skips_the_history(self):
        result = self.run_gap({"close": 100, "open": 100.01, "ltp": 100}, {"up_pct": 1})
        self.assertEqual(result["gap"]["direction"], "FLAT")
        self.assertFalse(result["historical"]["available"])

    def test_no_user_or_quote_is_none(self):
        self.assertIsNone(
            self.run_gap({"close": 100, "open": 100.5, "ltp": 101}, user=None)
        )
        self.assertIsNone(self.run_gap({}))
