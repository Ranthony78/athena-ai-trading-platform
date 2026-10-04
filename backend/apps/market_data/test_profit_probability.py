from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .services import black76
from .services import profit_probability_service as pp
from .services.core_calculations_service import compute as compute_core
from .services.snapshot_signals_service import RISK_FREE_RATE, _years_to_expiry
from .test_core_calculations import EXPIRY, NOW, SPOT, STRIKE, chain

IST = ZoneInfo("Asia/Kolkata")
ANCHOR = 10 * 60  # 10:00
FORWARD = 22453.0
VOL = 0.1227


def core_figures():
    return compute_core(SPOT, STRIKE, EXPIRY, NOW, chain(FORWARD, VOL))


def candle(day, minute, open_, close):
    return {
        "time": datetime(
            day.year, day.month, day.day, minute // 60, minute % 60, tzinfo=IST
        ),
        "open": open_,
        "close": close,
    }


def sessions(n, pct_move, horizon=30, base=22000.0):
    """n sessions: price at 10:00 is `base`, and it ends the horizon `pct_move` higher."""
    out = []
    first = date(2026, 6, 1)
    for i in range(n):
        day = first + timedelta(days=i)
        out.append(candle(day, ANCHOR, base, base))
        out.append(candle(day, ANCHOR + horizon - 15, base, base * (1 + pct_move)))
    return out


class BreakevenTests(SimpleTestCase):

    def moves(self, **overrides):
        t = _years_to_expiry(EXPIRY, NOW)
        args = dict(
            forward=FORWARD,
            strike=STRIKE,
            t_entry=t,
            rate=RISK_FREE_RATE,
            call_iv=VOL,
            put_iv=VOL,
            call_premium=156.95,
            put_premium=103.6,
            horizon_minutes=30,
            cost_per_leg=0.0,
        )
        args.update(overrides)
        return pp.breakeven_moves(**args)

    def test_call_breakeven_reprices_to_the_entry_premium(self):
        moves = self.moves()
        t_exit = _years_to_expiry(EXPIRY, NOW) - (30 / 375) / 365
        value = black76.price(
            FORWARD + moves["call"], STRIKE, t_exit, RISK_FREE_RATE, VOL, "CE"
        )
        self.assertAlmostEqual(value, 156.95, places=2)
        self.assertGreater(moves["call"], 0)
        self.assertLess(moves["put"], 0)
        self.assertGreater(moves["straddle_up"], 0)
        self.assertLess(moves["straddle_down"], 0)

    def test_longer_holds_costs_and_falling_iv_all_raise_the_hurdle(self):
        base = self.moves()
        self.assertGreater(self.moves(horizon_minutes=120)["call"], base["call"])
        self.assertGreater(self.moves(cost_per_leg=3.0)["call"], base["call"])
        self.assertGreater(self.moves(iv_shift=-2.0)["call"], base["call"])
        self.assertLess(self.moves(iv_shift=2.0)["call"], base["call"])

    def test_straddle_needs_a_bigger_move_than_either_leg_alone(self):
        moves = self.moves()
        self.assertGreater(moves["straddle_up"], moves["call"])
        self.assertLess(moves["straddle_down"], moves["put"])

    def test_expired_horizon_gives_nothing(self):
        moves = self.moves(t_entry=0.00001, horizon_minutes=375)
        self.assertTrue(all(v is None for v in moves.values()))


class HistoryTests(SimpleTestCase):

    def test_one_move_per_session_with_both_candles(self):
        moves = pp.history_moves(sessions(5, 0.01), ANCHOR, 30)
        self.assertEqual(len(moves), 5)
        self.assertAlmostEqual(moves[0], 0.01)

    def test_sessions_missing_a_candle_are_skipped(self):
        data = sessions(5, 0.01)
        data = [
            c
            for c in data
            if not (c["time"].date() == date(2026, 6, 2) and c["time"].minute == 15)
        ]
        self.assertEqual(len(pp.history_moves(data, ANCHOR, 30)), 4)

    def test_horizon_past_the_close_or_before_the_open_gives_nothing(self):
        self.assertEqual(pp.history_moves(sessions(5, 0.01), 15 * 60, 60), [])
        self.assertEqual(pp.history_moves(sessions(5, 0.01), 8 * 60, 30), [])


class ModelTests(SimpleTestCase):

    def test_tiny_move_is_close_to_a_coin_flip_each_way(self):
        up = pp.model_probability("up", 0.0001, 0.15, 30)
        down = pp.model_probability("down", -0.0001, 0.15, 30)
        self.assertAlmostEqual(up, 0.5, delta=0.02)
        self.assertAlmostEqual(down, 0.5, delta=0.02)

    def test_bigger_moves_are_less_likely_and_bad_input_is_none(self):
        small = pp.model_probability("up", 0.001, 0.15, 30)
        large = pp.model_probability("up", 0.01, 0.15, 30)
        self.assertGreater(small, large)
        self.assertIsNone(pp.model_probability("up", 0.01, 0, 30))
        self.assertIsNone(pp.model_probability("up", 1.5, 0.15, 30))


class ComputeTests(SimpleTestCase):

    def run_compute(self, candles, lot=65, core=None):
        return pp.compute(SPOT, core or core_figures(), lot, NOW, 30, ANCHOR, candles)

    def test_a_big_rise_every_session_favours_the_call(self):
        # +2% in 30 minutes clears every call and straddle hurdle, never the put's.
        result = self.run_compute(sessions(40, 0.02))

        self.assertTrue(result["available"])
        self.assertEqual(result["sessions"], 40)
        s = result["structures"]
        self.assertEqual(s["call"]["historical_pct"], 100.0)
        self.assertEqual(s["put"]["historical_pct"], 0.0)
        self.assertEqual(s["straddle"]["historical_pct"], 100.0)
        # Call and straddle tie at the top, so there is no clear highest.
        self.assertIsNone(result["highest"])

    def test_a_fall_every_session_favours_the_put_and_straddle(self):
        result = self.run_compute(sessions(40, -0.02))
        self.assertEqual(result["structures"]["put"]["historical_pct"], 100.0)
        self.assertEqual(result["structures"]["call"]["historical_pct"], 0.0)

    def test_a_flat_market_favours_nothing(self):
        result = self.run_compute(sessions(40, 0.0))
        for name in ("call", "put", "straddle"):
            self.assertEqual(result["structures"][name]["historical_pct"], 0.0)
        self.assertIsNone(result["highest"])

    def test_a_clear_leader_is_labelled(self):
        # A move between the call's hurdle and the straddle's bigger hurdle:
        # the call profits, the straddle and the put do not.
        core = core_figures()
        t = _years_to_expiry(EXPIRY, NOW)
        hurdles = pp.breakeven_moves(
            core["forward"],
            core["atm_strike"],
            t,
            RISK_FREE_RATE,
            core["call_iv"] / 100,
            core["put_iv"] / 100,
            core["call_price"],
            core["put_price"],
            30,
            2 * pp.BROKERAGE_PER_ORDER / 65,
        )
        middle = (hurdles["call"] + hurdles["straddle_up"]) / 2 / SPOT

        result = self.run_compute(sessions(40, middle))

        self.assertEqual(result["structures"]["call"]["historical_pct"], 100.0)
        self.assertEqual(result["structures"]["straddle"]["historical_pct"], 0.0)
        self.assertEqual(result["highest"], "call")

    def test_iv_range_brackets_the_base_case(self):
        result = self.run_compute(sessions(40, 0.0006))
        low, high = result["structures"]["call"]["iv_range_pct"]
        base = result["structures"]["call"]["historical_pct"]
        self.assertLessEqual(low, base)
        self.assertGreaterEqual(high, base)

    def test_too_few_sessions_gives_no_numbers(self):
        result = self.run_compute(sessions(10, 0.02))
        self.assertFalse(result["available"])
        self.assertIn("30", result["reason"])
        self.assertEqual(result["structures"], {})

    def test_missing_lot_size_or_iv_gives_no_numbers(self):
        self.assertFalse(self.run_compute(sessions(40, 0.02), lot=None)["available"])
        thin = {**core_figures(), "call_iv": None}
        self.assertFalse(self.run_compute(sessions(40, 0.02), core=thin)["available"])

    def test_brokerage_decides_a_move_that_only_just_clears_the_hurdle(self):
        core = core_figures()
        t = _years_to_expiry(EXPIRY, NOW)

        def hurdle(cost):
            return pp.breakeven_moves(
                core["forward"],
                core["atm_strike"],
                t,
                RISK_FREE_RATE,
                core["call_iv"] / 100,
                core["put_iv"] / 100,
                core["call_price"],
                core["put_price"],
                30,
                cost,
            )["call"]

        real_cost = 2 * pp.BROKERAGE_PER_ORDER / 65
        # Clears the hurdle without brokerage but not with it.
        between = (hurdle(0.0) + hurdle(real_cost)) / 2 / SPOT
        self.assertLess(hurdle(0.0), hurdle(real_cost))

        result = self.run_compute(sessions(40, between))

        self.assertEqual(result["structures"]["call"]["historical_pct"], 0.0)

    def test_costs_are_stated_in_the_assumptions(self):
        result = self.run_compute(sessions(40, 0.02))
        self.assertTrue(any("Brokerage" in line for line in result["assumptions"]))


class ProfitProbabilityEndpointTests(SimpleTestCase):
    """The view checks its input before doing any work."""

    def get(self, query, built=None):
        from unittest.mock import patch

        from django.contrib.auth import get_user_model
        from rest_framework.test import APIRequestFactory, force_authenticate

        from .api.views import ProfitProbabilityAPIView

        request = APIRequestFactory().get("/x/", query)
        force_authenticate(request, user=get_user_model()(username="t"))
        with patch.object(
            pp.ProfitProbabilityService, "build", return_value=built
        ) as build:
            response = ProfitProbabilityAPIView.as_view()(request, symbol="nifty")
        return response, build

    def test_a_bad_horizon_is_rejected_without_calculating(self):
        for horizon in ("7", "abc", "-5"):
            response, build = self.get({"horizon": horizon})
            self.assertFalse(response.data["success"])
            build.assert_not_called()

    def test_valid_request_passes_symbol_horizon_and_mode(self):
        response, build = self.get(
            {"horizon": "30", "mode": "NEXT_SESSION"}, built={"x": 1}
        )
        self.assertTrue(response.data["success"])
        build.assert_called_once()
        args = build.call_args.args
        self.assertEqual((args[0], args[2], args[3]), ("NIFTY", 30, "NEXT_SESSION"))

    def test_unknown_mode_falls_back_to_live(self):
        _, build = self.get({"horizon": "15", "mode": "bogus"}, built={"x": 1})
        self.assertEqual(build.call_args.args[3], "LIVE")

    def test_no_option_data_is_an_error_message(self):
        response, _ = self.get({"horizon": "15"}, built=None)
        self.assertFalse(response.data["success"])
