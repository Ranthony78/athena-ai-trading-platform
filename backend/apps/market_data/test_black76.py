import math
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .services import black76
from .services.option_chain_service import OptionChainService

F, K, T, R, VOL = 100.0, 100.0, 1.0, 0.05, 0.20


class PriceTests(SimpleTestCase):

    def test_atm_call_matches_reference_value(self):
        # 100 * e^-0.05 * (N(0.1) - N(-0.1))
        self.assertAlmostEqual(black76.price(F, K, T, R, VOL, "CE"), 7.5773, places=3)

    def test_put_call_parity_holds(self):
        call = black76.price(F, 95.0, T, R, VOL, "CE")
        put = black76.price(F, 95.0, T, R, VOL, "PE")
        self.assertAlmostEqual(call - put, math.exp(-R * T) * (F - 95.0), places=8)

    def test_zero_vol_is_discounted_intrinsic(self):
        self.assertAlmostEqual(
            black76.price(110, 100, 1, 0.05, 0, "CE"), math.exp(-0.05) * 10, places=8
        )
        self.assertEqual(black76.price(90, 100, 1, 0.05, 0, "CE"), 0)

    def test_bad_inputs_are_none(self):
        self.assertIsNone(black76.price(0, K, T, R, VOL, "CE"))
        self.assertIsNone(black76.price(F, K, 0, R, VOL, "CE"))
        self.assertIsNone(black76.price(F, K, T, R, -0.1, "CE"))
        self.assertIsNone(black76.price(F, K, T, float("nan"), VOL, "CE"))


class ImpliedVolTests(SimpleTestCase):

    def test_round_trip_across_strikes_and_sides(self):
        for strike in (80, 95, 100, 105, 130):
            for side in ("CE", "PE"):
                model = black76.price(F, strike, 0.25, R, 0.35, side)
                iv = black76.implied_vol(model, F, strike, 0.25, R, side)
                self.assertAlmostEqual(iv, 0.35, places=4, msg=f"{strike}{side}")

    def test_price_below_intrinsic_is_none(self):
        intrinsic = math.exp(-R * T) * 20
        self.assertIsNone(black76.implied_vol(intrinsic - 0.5, 120, 100, T, R, "CE"))

    def test_price_beyond_any_volatility_is_none(self):
        self.assertIsNone(black76.implied_vol(500, F, K, T, R, "CE"))

    def test_unusable_inputs_are_none(self):
        for args in ((0, F, K, T, R), (5, 0, K, T, R), (5, F, K, 0, R)):
            self.assertIsNone(black76.implied_vol(*args, "CE"))


class GreeksTests(SimpleTestCase):

    def test_delta_gamma_vega_match_finite_differences(self):
        g = black76.greeks(F, K, T, R, VOL, "CE")
        h = 0.01
        up = black76.price(F + h, K, T, R, VOL, "CE")
        down = black76.price(F - h, K, T, R, VOL, "CE")
        mid = black76.price(F, K, T, R, VOL, "CE")
        self.assertAlmostEqual(g["delta"], (up - down) / (2 * h), places=4)
        self.assertAlmostEqual(g["gamma"], (up - 2 * mid + down) / h**2, places=4)
        dv = 0.0001
        vega = (
            black76.price(F, K, T, R, VOL + dv, "CE")
            - black76.price(F, K, T, R, VOL - dv, "CE")
        ) / (2 * dv)
        self.assertAlmostEqual(g["vega"], vega / 100, places=4)

    def test_theta_matches_one_day_decay(self):
        g = black76.greeks(F, K, T, R, VOL, "PE")
        dt = 1 / 365
        change = black76.price(F, K, T - dt, R, VOL, "PE") - black76.price(
            F, K, T, R, VOL, "PE"
        )
        self.assertAlmostEqual(g["theta"], change, places=3)

    def test_put_delta_is_negative_and_bad_vol_is_none(self):
        self.assertLess(black76.greeks(F, K, T, R, VOL, "PE")["delta"], 0)
        self.assertIsNone(black76.greeks(F, K, T, R, 0, "CE"))


def chain_from_forward(forward, strikes, t=0.05, rate=0.06, vol=0.18):
    rows = []
    for strike in strikes:
        for side in ("CE", "PE"):
            rows.append(
                {
                    "strike": strike,
                    "option_type": side,
                    "ltp": black76.price(forward, strike, t, rate, vol, side),
                }
            )
    return rows


class ParityForwardTests(SimpleTestCase):

    def test_recovers_the_forward_the_chain_was_priced_from(self):
        # A long expiry and high rate, so ignoring the discounting would show.
        rows = chain_from_forward(24150.0, range(23800, 24600, 100), t=1.0, rate=0.10)
        result = black76.parity_forward(rows, 24100.0, 1.0, 0.10)
        self.assertAlmostEqual(result, 24150.0, delta=0.5)

    def test_needs_a_priced_call_and_put_at_the_same_strike(self):
        rows = [
            {"strike": 100, "option_type": "CE", "ltp": 5},
            {"strike": 110, "option_type": "PE", "ltp": 5},
        ]
        self.assertIsNone(black76.parity_forward(rows, 100, 0.05, 0.06))

    def test_unpriced_legs_are_ignored(self):
        rows = [
            {"strike": 100, "option_type": "CE", "ltp": 0},
            {"strike": 100, "option_type": "PE", "ltp": 4},
        ]
        self.assertIsNone(black76.parity_forward(rows, 100, 0.05, 0.06))

    def test_bad_spot_or_time_is_none(self):
        rows = chain_from_forward(24150.0, [24100, 24200])
        self.assertIsNone(black76.parity_forward(rows, 0, 0.05, 0.06))
        self.assertIsNone(black76.parity_forward(rows, 24100, 0, 0.06))


class ChainIntegrationTests(SimpleTestCase):

    def enrich(self, forward):
        row = {
            "strike": 24100.0,
            "option_type": "CE",
            "ltp": black76.price(24150.0, 24100.0, 0.05, 0.06, 0.18, "CE"),
        }
        return OptionChainService()._enrich_row(row, 24100.0, 0.05, 0.06, forward)

    def test_with_a_forward_the_row_uses_black76(self):
        row = self.enrich(24150.0)
        self.assertEqual(row["iv_model"], "black76")
        self.assertAlmostEqual(row["iv"], 18.0, places=1)

    def test_without_a_forward_it_falls_back_and_says_so(self):
        row = self.enrich(None)
        self.assertEqual(row["iv_model"], "black_scholes")

    def get_chain(self, model):
        from datetime import date
        from types import SimpleNamespace

        rows = chain_from_forward(24150.0, range(23900, 24400, 100), t=0.05, rate=0.06)
        for row in rows:
            row["expiry"] = "2026-10-08"
        market = SimpleNamespace(
            quote=lambda symbol: {"ltp": 24100.0},
            option_chain=lambda symbol, expiry=None: rows,
        )
        with (
            override_settings(OPTION_IV_MODEL=model, MARKET_PROVIDER="zerodha"),
            patch(
                "apps.market_data.services.market_service.MarketService",
                return_value=market,
            ),
            patch.object(
                OptionChainService,
                "_get_available_expiries",
                return_value=[date(2026, 10, 8)],
            ),
            patch.object(
                OptionChainService, "_time_to_expiry_years", return_value=0.05
            ),
        ):
            return OptionChainService().get_chain("NIFTY")

    def test_get_chain_uses_black76_only_when_the_setting_asks(self):
        self.assertEqual(
            {r["iv_model"] for r in self.get_chain("black76")}, {"black76"}
        )
        self.assertEqual(
            {r["iv_model"] for r in self.get_chain("black_scholes")}, {"black_scholes"}
        )

    def test_black76_recovers_the_vol_the_chain_was_priced_with(self):
        for row in self.get_chain("black76"):
            self.assertAlmostEqual(row["iv"], 18.0, delta=0.1)
