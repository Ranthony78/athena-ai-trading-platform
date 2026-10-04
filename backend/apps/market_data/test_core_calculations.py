import math
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .services import black76
from .services.core_calculations_service import compute, realized_vol, vix_session_move
from .services.snapshot_signals_service import RISK_FREE_RATE, _years_to_expiry

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 10, 1, 15, 39, tzinfo=IST)
EXPIRY = date(2026, 10, 6)
SPOT = 22421.95
STRIKE = 22400.0


def chain(forward, vol, strikes=range(22200, 22700, 100)):
    t = _years_to_expiry(EXPIRY, NOW)
    rows = []
    for strike in strikes:
        for side in ("CE", "PE"):
            rows.append(
                {
                    "strike": float(strike),
                    "option_type": side,
                    "ltp": round(
                        black76.price(forward, strike, t, RISK_FREE_RATE, vol, side), 2
                    ),
                }
            )
    return rows


def simple_rows(call=156.95, put=103.6):
    return [
        {"strike": STRIKE, "option_type": "CE", "ltp": call},
        {"strike": STRIKE, "option_type": "PE", "ltp": put},
    ]


class RequiredMoveTests(SimpleTestCase):
    """Reference values from the analysis report for the 1 Oct close."""

    def setUp(self):
        self.result = compute(SPOT, STRIKE, EXPIRY, NOW, simple_rows())

    def test_straddle_and_percent_of_spot(self):
        self.assertEqual(self.result["straddle"], 260.55)
        self.assertEqual(self.result["straddle_pct_of_spot"], 1.16)

    def test_required_moves(self):
        moves = self.result["required_move"]
        self.assertAlmostEqual(moves["call"], 135.0, delta=0.05)
        self.assertAlmostEqual(moves["put"], -125.6, delta=0.1)
        self.assertAlmostEqual(moves["straddle_up"], 238.6, delta=0.05)
        self.assertAlmostEqual(moves["straddle_down"], -282.5, delta=0.05)

    def test_without_a_forward_black76_figures_are_none(self):
        # One strike cannot give a parity forward from several strikes' pairs,
        # but a single paired strike still can; remove the put to break it.
        result = compute(SPOT, STRIKE, EXPIRY, NOW, simple_rows()[:1])
        self.assertIsNone(result["forward"])
        self.assertIsNone(result["implied_vol"])
        self.assertIsNone(result["straddle"])
        self.assertAlmostEqual(result["required_move"]["call"], 135.0, delta=0.05)


class Black76Tests(SimpleTestCase):

    def setUp(self):
        self.rows = chain(22453.0, 0.1227)
        self.result = compute(SPOT, STRIKE, EXPIRY, NOW, self.rows)

    def test_forward_and_iv_are_recovered(self):
        self.assertAlmostEqual(self.result["forward"], 22453.0, delta=2.0)
        self.assertAlmostEqual(self.result["implied_vol"], 12.27, delta=0.1)
        self.assertAlmostEqual(self.result["call_iv"], 12.27, delta=0.15)
        self.assertAlmostEqual(self.result["put_iv"], 12.27, delta=0.15)

    def test_straddle_greeks_are_consistent(self):
        greeks = self.result["straddle_greeks"]
        self.assertLess(greeks["theta_per_day"], 0)
        self.assertAlmostEqual(
            greeks["theta_per_15_min"], greeks["theta_per_day"] / 25, delta=0.01
        )
        self.assertGreater(greeks["gamma"], 0)
        self.assertGreater(greeks["vega_per_vol_point"], 0)

    def test_iv_velocity_is_passed_through(self):
        result = compute(
            SPOT,
            STRIKE,
            EXPIRY,
            NOW,
            self.rows,
            iv_velocity={"change_per_window": -1.62},
        )
        self.assertEqual(result["iv_velocity"], {"change_per_window": -1.62})

    def test_missing_spot_strike_or_expiry_gives_empty_result(self):
        for args in (
            (None, STRIKE, EXPIRY),
            (SPOT, None, EXPIRY),
            (SPOT, STRIKE, None),
        ):
            result = compute(*args, NOW, self.rows)
            self.assertIsNone(result["forward"])
            self.assertIsNone(result["straddle"])


class VixAndRealizedVolTests(SimpleTestCase):

    def test_one_session_move_from_vix(self):
        self.assertAlmostEqual(vix_session_move(SPOT, 14.46), 204.2, delta=0.1)

    def test_bad_inputs_are_none(self):
        self.assertIsNone(vix_session_move(SPOT, None))
        self.assertIsNone(vix_session_move(SPOT, 0))
        self.assertIsNone(vix_session_move(0, 14.0))

    def test_realized_vol_of_alternating_returns(self):
        closes = [100.0]
        for i in range(10):
            closes.append(closes[-1] * (1.01 if i % 2 == 0 else 1 / 1.01))
        expected = (
            math.sqrt(10 / 9) * math.log(1.01) * math.sqrt(252) * 100
        )  # sample stdev of +-ln(1.01)
        self.assertAlmostEqual(realized_vol(closes), expected, delta=0.05)

    def test_flat_prices_have_zero_vol(self):
        self.assertEqual(realized_vol([100.0] * 11), 0.0)

    def test_too_few_or_bad_closes_are_none(self):
        self.assertIsNone(realized_vol([100.0] * 10))
        self.assertIsNone(realized_vol([100.0] * 10 + [0]))


class FromContextTests(SimpleTestCase):
    """Figures built from the option data the analysis prompt already fetched."""

    def options(self, rows):
        return {
            "spot_price": SPOT,
            "atm_strike": STRIKE,
            "expiry": EXPIRY.isoformat(),
            "core_rows": rows,
        }

    def run_from_context(self, options, vix=14.46):
        from unittest.mock import patch

        from .services.core_calculations_service import CoreCalculationsService

        with (
            patch.object(CoreCalculationsService, "_daily_closes", return_value=[]),
            patch.object(CoreCalculationsService, "_iv_velocity", return_value=None),
            patch("django.utils.timezone.now", return_value=NOW),
        ):
            return CoreCalculationsService.from_context("NIFTY", options, vix)

    def test_computes_from_prompt_rows_without_another_chain_request(self):
        result = self.run_from_context(self.options(chain(22453.0, 0.1227)))

        self.assertAlmostEqual(result["implied_vol"], 12.27, delta=0.2)
        self.assertAlmostEqual(result["vix_session_move"], 204.2, delta=0.1)

    def test_missing_options_or_rows_is_none(self):
        self.assertIsNone(self.run_from_context(None))
        self.assertIsNone(self.run_from_context(self.options([])))
