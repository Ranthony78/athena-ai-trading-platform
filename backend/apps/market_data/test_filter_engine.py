from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .services.filter_engine_service import EngineParameters, evaluate

IST = ZoneInfo("Asia/Kolkata")
MORNING = datetime(2026, 10, 5, 11, 0, tzinfo=IST)


def core(**overrides):
    """The reference run: falling IV, wide required moves, realized above implied."""
    base = {
        "iv_velocity": {"change_per_window": -0.40, "window_minutes": 15},
        "straddle_greeks": {"theta_per_15_min": -1.01, "vega_per_vol_point": 20.7},
        "vix_session_move": 204.0,
        "required_move": {
            "call": 135.0,
            "put": -125.6,
            "straddle_up": 238.6,
            "straddle_down": -282.5,
        },
        "realized_vol": 14.05,
        "implied_vol": 12.27,
    }
    base.update(overrides)
    return base


def signals(oi=(-47.0, -39.0), spread=None):
    return {
        "oi_change": {
            "CE": {"change_pct": oi[0]} if oi[0] is not None else None,
            "PE": {"change_pct": oi[1]} if oi[1] is not None else None,
        },
        "spread_tightening": spread or {"CE": None, "PE": None},
    }


_DEFAULT = object()


def run(
    core_=None, signals_=_DEFAULT, now=MORNING, market_open=True, mode="LIVE", **kw
):
    return evaluate(
        core() if core_ is None else core_,
        signals() if signals_ is _DEFAULT else signals_,
        now,
        market_open,
        mode,
        **kw,
    )


def status(result, key):
    return next(f["status"] for f in result["filters"] if f["key"] == key)


class ReferenceRunTests(SimpleTestCase):
    """The reference engine scored this situation 3 of 6 with F not applicable."""

    def test_closed_market_reference_scores_three_of_six(self):
        result = run(market_open=False)

        self.assertEqual(status(result, "A"), "fail")
        self.assertEqual(status(result, "B"), "pass")
        self.assertEqual(status(result, "C"), "pass")
        self.assertEqual(status(result, "D"), "pass")
        self.assertEqual(status(result, "E"), "not_evaluable")
        self.assertEqual(status(result, "F"), "not_applicable")
        self.assertEqual(result["passed"], 3)
        self.assertEqual(result["verdict"], "NO_TRADE")

    def test_unknown_and_not_applicable_are_never_passes(self):
        result = run(market_open=False)
        counted = [f for f in result["filters"] if f["status"] == "pass"]
        self.assertEqual(len(counted), result["passed"])


class FilterATests(SimpleTestCase):

    def test_rising_iv_worth_more_than_theta_passes(self):
        fast = core(iv_velocity={"change_per_window": 0.5, "window_minutes": 15})
        self.assertEqual(status(run(fast), "A"), "pass")

    def test_rising_but_too_slowly_fails(self):
        slow = core(iv_velocity={"change_per_window": 0.01, "window_minutes": 15})
        self.assertEqual(status(run(slow), "A"), "fail")

    def test_falling_iv_fails_with_an_explanation(self):
        result = run()
        a = next(f for f in result["filters"] if f["key"] == "A")
        self.assertIn("not rising", a["detail"])

    def test_the_window_scales_theta(self):
        # The same IV change is worth ₹2.07. Over 15 minutes theta is ₹1.01 and
        # the bar is ₹0.61; over 60 minutes theta is ₹4.04 and the bar is ₹2.42.
        quick = core(iv_velocity={"change_per_window": 0.1, "window_minutes": 15})
        slow = core(iv_velocity={"change_per_window": 0.1, "window_minutes": 60})
        self.assertEqual(status(run(quick), "A"), "pass")
        self.assertEqual(status(run(slow), "A"), "fail")

    def test_missing_history_is_not_evaluable(self):
        self.assertEqual(status(run(core(iv_velocity=None)), "A"), "not_evaluable")
        self.assertEqual(status(run(core(straddle_greeks=None)), "A"), "not_evaluable")


class FilterBTests(SimpleTestCase):

    def test_passes_if_any_structure_qualifies(self):
        result = run()
        b = next(f for f in result["filters"] if f["key"] == "B")
        self.assertIn("straddle needs 215 (fail)", b["detail"])
        self.assertIn("call needs 122 (pass)", b["detail"])

    def test_fails_when_no_structure_qualifies(self):
        self.assertEqual(status(run(core(vix_session_move=50.0)), "B"), "fail")

    def test_missing_vix_or_moves_is_not_evaluable(self):
        self.assertEqual(status(run(core(vix_session_move=None)), "B"), "not_evaluable")
        empty = core(
            required_move={
                "call": None,
                "put": None,
                "straddle_up": None,
                "straddle_down": None,
            }
        )
        self.assertEqual(status(run(empty), "B"), "not_evaluable")


class FilterCDETests(SimpleTestCase):

    def test_c_needs_a_big_enough_oi_change_either_way(self):
        self.assertEqual(status(run(signals_=signals(oi=(2.0, -3.0))), "C"), "fail")
        self.assertEqual(status(run(signals_=signals(oi=(2.0, 6.0))), "C"), "pass")
        self.assertEqual(status(run(signals_=signals(oi=(-5.0, None))), "C"), "pass")
        self.assertEqual(
            status(run(signals_=signals(oi=(None, None))), "C"), "not_evaluable"
        )
        self.assertEqual(status(run(signals_=None), "C"), "not_evaluable")

    def test_d_compares_realized_to_implied(self):
        self.assertEqual(status(run(core(realized_vol=10.0)), "D"), "fail")
        self.assertEqual(status(run(core(realized_vol=11.2)), "D"), "pass")
        self.assertEqual(status(run(core(realized_vol=None)), "D"), "not_evaluable")
        self.assertEqual(status(run(core(implied_vol=None)), "D"), "not_evaluable")

    def test_e_needs_every_evaluable_leg_to_tighten(self):
        tight = {"change_pct": -25.0, "tightening": True}
        wide = {"change_pct": 8.0, "tightening": False}
        self.assertEqual(
            status(run(signals_=signals(spread={"CE": tight, "PE": tight})), "E"),
            "pass",
        )
        self.assertEqual(
            status(run(signals_=signals(spread={"CE": tight, "PE": None})), "E"), "pass"
        )
        self.assertEqual(
            status(run(signals_=signals(spread={"CE": tight, "PE": wide})), "E"), "fail"
        )
        self.assertEqual(
            status(run(signals_=signals(spread={"CE": None, "PE": None})), "E"),
            "not_evaluable",
        )
        small = {"change_pct": -4.0, "tightening": True}
        self.assertEqual(
            status(run(signals_=signals(spread={"CE": small, "PE": small})), "E"),
            "fail",
        )


class FilterFTests(SimpleTestCase):

    def at(self, hour, minute):
        return datetime(2026, 10, 5, hour, minute, tzinfo=IST)

    def test_before_the_last_entry_passes_and_at_it_fails(self):
        self.assertEqual(status(run(now=self.at(13, 59)), "F"), "pass")
        self.assertEqual(status(run(now=self.at(14, 0)), "F"), "fail")
        self.assertEqual(status(run(now=self.at(14, 45)), "F"), "fail")

    def test_closed_market_and_next_session_are_not_applicable(self):
        self.assertEqual(status(run(market_open=False), "F"), "not_applicable")
        self.assertEqual(status(run(mode="NEXT_SESSION"), "F"), "not_applicable")

    def test_time_is_judged_in_ist(self):
        utc_morning = datetime(2026, 10, 5, 8, 0, tzinfo=ZoneInfo("UTC"))  # 13:30 IST
        self.assertEqual(status(run(now=utc_morning), "F"), "pass")
        utc_after = datetime(2026, 10, 5, 9, 0, tzinfo=ZoneInfo("UTC"))  # 14:30 IST
        self.assertEqual(status(run(now=utc_after), "F"), "fail")


class VerdictTests(SimpleTestCase):

    def four_pass(self, **kw):
        # Open market at 11:00 with the reference data: B, C, D and F pass, A fails.
        return run(**kw)

    def test_four_passes_meet_the_filters(self):
        result = self.four_pass()
        self.assertEqual(result["passed"], 4)
        self.assertEqual(result["verdict"], "CONDITIONS_MET")
        self.assertIsNone(result["highest_structure"])
        self.assertIn(
            "no structure has a clear historical lead", result["verdict_text"]
        )

    def test_the_historical_leader_is_named_only_when_filters_are_met(self):
        met = self.four_pass(profit_probability={"highest": "put"})
        self.assertEqual(met["highest_structure"], "put")
        self.assertIn("put", met["verdict_text"])

        unmet = run(market_open=False, profit_probability={"highest": "put"})
        self.assertEqual(unmet["passed"], 3)
        self.assertEqual(unmet["verdict"], "NO_TRADE")
        self.assertIsNone(unmet["highest_structure"])

    def test_the_required_count_is_a_parameter(self):
        lenient = run(market_open=False, params=EngineParameters(min_passes=3))
        self.assertEqual(lenient["verdict"], "CONDITIONS_MET")

    def test_proposed_thresholds_are_labelled(self):
        sources = {f["key"]: f["threshold_source"] for f in run()["filters"]}
        self.assertEqual(
            sources,
            {
                "A": "reference",
                "B": "reference",
                "C": "proposed",
                "D": "proposed",
                "E": "proposed",
                "F": "reference",
            },
        )

    def test_parameters_are_reported(self):
        params = run()["parameters"]
        self.assertEqual(params["min_passes"], 4)
        self.assertEqual(params["last_entry"], "14:00")
        self.assertEqual(EngineParameters().last_entry, time(14, 0))


class OptionsEngineEndpointTests(SimpleTestCase):

    def get(self, query, built=None):
        from unittest.mock import patch

        from django.contrib.auth import get_user_model
        from rest_framework.test import APIRequestFactory, force_authenticate

        from .api.views import OptionsEngineAPIView
        from .services import filter_engine_service as module

        request = APIRequestFactory().get("/x/", query)
        force_authenticate(request, user=get_user_model()(username="t"))
        with patch.object(
            module.FilterEngineService, "build", return_value=built
        ) as build:
            response = OptionsEngineAPIView.as_view()(request, symbol="banknifty")
        return response, build

    def test_bad_horizon_is_rejected_before_any_work(self):
        response, build = self.get({"horizon": "5"})
        self.assertFalse(response.data["success"])
        build.assert_not_called()

    def test_valid_request_reaches_the_service(self):
        response, build = self.get(
            {"horizon": "60", "mode": "NEXT_SESSION"}, built={"engine": {}}
        )
        self.assertTrue(response.data["success"])
        self.assertEqual(build.call_args.args[0], "BANKNIFTY")
        self.assertEqual(build.call_args.args[2:], (60, "NEXT_SESSION"))

    def test_no_option_data_is_an_error(self):
        response, _ = self.get({"horizon": "15"}, built=None)
        self.assertFalse(response.data["success"])
