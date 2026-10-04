from unittest.mock import patch

from django.test import SimpleTestCase

from .services.deterministic_metrics_service import DeterministicMetricsService

DAILY = "apps.market_data.services.daily_levels_service.DailyLevelsService.levels"
FUT = "apps.market_data.services.futures_service.FuturesService.snapshot"
GAP = "apps.market_data.services.analysis_report_service.AnalysisReportService._get_gap_analysis"
BLOCKS = "apps.market_data.services.time_block_service.TimeBlockService.build"
SIGNALS = (
    "apps.market_data.services.snapshot_signals_service.SnapshotSignalsService.compute"
)
CORE = "apps.market_data.services.core_calculations_service.CoreCalculationsService.from_context"


def build(**kwargs):
    defaults = dict(
        symbol="NIFTY", user=object(), quote=None, vix=None, candles=[], options=None
    )
    return DeterministicMetricsService.build(**{**defaults, **kwargs})


def quiet(**overrides):
    """Patch every data source the builder reads; override the ones under test."""
    from contextlib import ExitStack

    values = {
        DAILY: None,
        FUT: None,
        GAP: None,
        BLOCKS: None,
        SIGNALS: None,
        CORE: None,
    }
    values.update(overrides)
    stack = ExitStack()
    for target, value in values.items():
        stack.enter_context(patch(target, return_value=value))
    return stack


class BuildTests(SimpleTestCase):

    def test_everything_missing_is_none_not_an_error(self):
        with quiet():
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
        with quiet():
            metrics = build(
                quote=quote, vix=vix, options={"oi_walls": {"call_wall": 1}}
            )
        self.assertEqual(metrics["gap_retrace"]["retrace_pct"], 50.0)
        self.assertEqual(metrics["vix_change_pct"], 20.0)
        self.assertEqual(metrics["vix_intraday_high"], 12.5)
        self.assertEqual(metrics["oi_walls"], {"call_wall": 1})

    def test_one_failing_section_does_not_break_the_rest(self):
        with quiet(**{FUT: {"ltp": 5}}), patch(DAILY, side_effect=RuntimeError("boom")):
            metrics = build()
        self.assertIsNone(metrics["daily_levels"])
        self.assertEqual(metrics["futures"], {"ltp": 5})

    def test_new_sections_are_gathered_and_isolated(self):
        core = {"forward": 22453.0, "implied_vol": 12.27}
        with (
            quiet(**{CORE: core, BLOCKS: {"blocks": []}}),
            patch(SIGNALS, side_effect=RuntimeError("no history")),
        ):
            metrics = build(options={"core_rows": [1]}, vix={"ltp": 14.5})

        self.assertEqual(metrics["core_calculations"], core)
        self.assertEqual(metrics["time_blocks"], {"blocks": []})
        self.assertIsNone(metrics["snapshot_signals"])
        self.assertIsNone(metrics["gap_history"])


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


class NewPromptLinesTests(SimpleTestCase):

    METRICS = {
        "core_calculations": {
            "forward": 22453.0,
            "implied_vol": 12.27,
            "straddle": 260.55,
            "required_move": {
                "call": 135.0,
                "put": -125.6,
                "straddle_up": 238.6,
                "straddle_down": -282.5,
            },
            "straddle_greeks": {
                "theta_per_day": -25.35,
                "gamma": 0.00244,
                "vega_per_vol_point": 20.7,
            },
            "iv_velocity": {"change_per_window": -1.62, "window_minutes": 15},
            "vix_session_move": 204.2,
            "realized_vol": 14.05,
        },
        "gap_history": {
            "historical": {
                "continuation_pct": 55.0,
                "reversal_pct": 37.0,
                "flat_pct": 8.0,
                "sample_size": 40,
            }
        },
        "snapshot_signals": {
            "oi_change": {"CE": {"change_pct": -47.0}, "PE": {"change_pct": -39.0}},
            "volume_spike": {"CE": {"ratio": 3.0}, "PE": None},
        },
        "time_blocks": {
            "blocks": [
                {
                    "window": "09:15 – 10:30",
                    "bias": "Leans down",
                    "volatility": "High",
                    "trend_strength": "Moderate",
                    "sessions": 14,
                }
            ]
        },
    }

    def test_values_appear_in_the_prompt_text(self):
        text = DeterministicMetricsService.as_prompt_text(self.METRICS)
        for expected in (
            "parity forward 22453.0",
            "implied volatility 12.27%",
            "call 135.0, put -125.6",
            "continued 55.0%",
            "call -47.0%",
            "call 3.0x, put NA",
            "09:15 – 10:30: Leans down",
            "Straddle theta/day -25.35",
        ):
            self.assertIn(expected, text)

    def test_missing_sections_print_na_not_none(self):
        text = DeterministicMetricsService.as_prompt_text({})
        self.assertIn("implied volatility NA%", text)
        self.assertIn("Time blocks (descriptive history): NA", text)
        self.assertNotIn("None", text)


class ProfitProbabilityLineTests(SimpleTestCase):

    PROFIT = {
        "profit_probability": {
            "horizon_minutes": 30,
            "sessions": 96,
            "structures": {
                "call": {"historical_pct": 31.2},
                "put": {"historical_pct": 33.3},
                "straddle": {"historical_pct": 24.0},
            },
        }
    }

    def test_values_and_horizon_appear_in_the_prompt_text(self):
        text = DeterministicMetricsService.as_prompt_text(self.PROFIT)
        for expected in (
            "held 30 min",
            "96 sessions",
            "call 31.2%",
            "put 33.3%",
            "straddle 24.0%",
        ):
            self.assertIn(expected, text)

    def test_missing_probability_prints_na(self):
        text = DeterministicMetricsService.as_prompt_text({})
        self.assertIn("call NA%, put NA%, straddle NA%", text)

    def test_it_is_only_requested_with_core_figures_and_a_horizon(self):
        from unittest.mock import patch

        target = (
            "apps.market_data.services.profit_probability_service."
            "ProfitProbabilityService.from_core"
        )
        with quiet(), patch(target, return_value={"structures": {}}) as called:
            no_horizon = build(options={"core_rows": [1]})
            self.assertIsNone(no_horizon["profit_probability"])
            called.assert_not_called()

        with (
            quiet(**{CORE: {"forward": 1.0}}),
            patch(target, return_value={"structures": {}}) as called,
        ):
            with_horizon = build(
                options={"core_rows": [1]}, horizon_minutes=30, analysis_mode="LIVE"
            )
            self.assertEqual(with_horizon["profit_probability"], {"structures": {}})
            self.assertEqual(called.call_args.args[2:], (30, "LIVE"))


class FilterEngineLineTests(SimpleTestCase):

    ENGINE = {
        "filter_engine": {
            "passed": 3,
            "required": 4,
            "verdict_text": "No trade: 3 of 6 filters passed; 4 are required.",
            "filters": [
                {"key": "A", "status": "fail"},
                {"key": "B", "status": "pass"},
                {"key": "E", "status": "not_evaluable"},
                {"key": "F", "status": "not_applicable"},
            ],
        }
    }

    def test_prompt_line_lists_each_filter_and_the_verdict(self):
        text = DeterministicMetricsService.as_prompt_text(self.ENGINE)
        for expected in (
            "3 of 6 passed",
            "A fail",
            "B pass",
            "E not evaluable",
            "F not applicable",
            "No trade: 3 of 6 filters passed",
        ):
            self.assertIn(expected, text)

    def test_missing_engine_prints_na(self):
        text = DeterministicMetricsService.as_prompt_text({})
        self.assertIn("NA of 6 passed", text)
        self.assertNotIn("None", text)

    def test_engine_runs_only_with_core_figures(self):
        from unittest.mock import patch

        evaluate = "apps.market_data.services.filter_engine_service.evaluate"
        session = "apps.market_data.engine.market_state.MarketState.session_info"
        with quiet(), patch(evaluate, return_value={"passed": 0}) as called:
            self.assertIsNone(build()["filter_engine"])
            called.assert_not_called()

        with (
            quiet(**{CORE: {"forward": 1.0}}),
            patch(evaluate, return_value={"passed": 2}) as called,
            patch(session, return_value={"is_live": False}),
        ):
            result = build(options={"core_rows": [1]}, analysis_mode="NEXT_SESSION")
            self.assertEqual(result["filter_engine"], {"passed": 2})
            self.assertEqual(called.call_args.args[3:5], (False, "NEXT_SESSION"))
