from unittest.mock import patch

from django.test import SimpleTestCase

from .services.deterministic_metrics_service import DeterministicMetricsService

DAILY = "apps.market_data.services.daily_levels_service.DailyLevelsService.levels"
FUT = "apps.market_data.services.futures_service.FuturesService.snapshot"


def build(**kwargs):
    defaults = dict(
        symbol="NIFTY", user=object(), quote=None, vix=None, candles=[], options=None
    )
    return DeterministicMetricsService.build(**{**defaults, **kwargs})


class BuildTests(SimpleTestCase):

    def test_everything_missing_is_none_not_an_error(self):
        with patch(DAILY, return_value=None), patch(FUT, return_value=None):
            metrics = build()
        self.assertTrue(
            all(
                metrics[k] is None
                for k in (
                    "daily_levels",
                    "gap_retrace",
                    "vix_change_pct",
                    "volume_confirmation",
                    "futures",
                    "oi_walls",
                )
            )
        )

    def test_values_are_computed(self):
        quote = {"ltp": 101, "open": 102, "close": 100}
        vix = {"ltp": 12.0, "close": 10.0, "high": 12.5}
        with patch(DAILY, return_value=None), patch(FUT, return_value=None):
            metrics = build(
                quote=quote, vix=vix, options={"oi_walls": {"call_wall": 1}}
            )
        self.assertEqual(metrics["gap_retrace"]["retrace_pct"], 50.0)
        self.assertEqual(metrics["vix_change_pct"], 20.0)
        self.assertEqual(metrics["vix_intraday_high"], 12.5)
        self.assertEqual(metrics["oi_walls"], {"call_wall": 1})

    def test_one_failing_section_does_not_break_the_rest(self):
        with (
            patch(DAILY, side_effect=RuntimeError("boom")),
            patch(FUT, return_value={"ltp": 5}),
        ):
            metrics = build()
        self.assertIsNone(metrics["daily_levels"])
        self.assertEqual(metrics["futures"], {"ltp": 5})


class PromptTextTests(SimpleTestCase):

    def test_missing_metrics_print_na(self):
        text = DeterministicMetricsService.as_prompt_text(None)
        self.assertIn("VWAP NA", text)
        self.assertIn("call NA", text)
        self.assertNotIn("None", text)

    def test_present_values_print(self):
        text = DeterministicMetricsService.as_prompt_text(
            {"futures": {"contract": "NIFTYFUT", "vwap": 24050.0}}
        )
        self.assertIn("NIFTYFUT", text)
        self.assertIn("VWAP 24050.0", text)
