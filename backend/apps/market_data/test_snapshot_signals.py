from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, TestCase

from .models import Instrument, OptionSnapshot
from .services import black76
from .services import snapshot_signals_service as signals
from .services.snapshot_signals_service import SnapshotSignalsService

IST = ZoneInfo("Asia/Kolkata")
T0 = datetime(2026, 10, 5, 10, 0, tzinfo=IST)


def pt(minutes, **values):
    base = {
        "t": T0 + timedelta(minutes=minutes),
        "ltp": 100.0,
        "bid": 99.0,
        "ask": 101.0,
    }
    base.update({"volume": 0, "oi": 1000})
    return {**base, **values}


class OiChangeTests(SimpleTestCase):

    def test_change_against_the_baseline_15_minutes_back(self):
        points = [pt(0, oi=1000), pt(5, oi=1100), pt(10, oi=1150), pt(15, oi=1200)]
        result = signals.oi_change(points)
        self.assertEqual(result["change"], 200)
        self.assertEqual(result["change_pct"], 20.0)

    def test_no_baseline_near_the_window_is_none(self):
        # Latest and previous are only 5 minutes apart.
        self.assertIsNone(signals.oi_change([pt(0), pt(5)]))
        self.assertIsNone(signals.oi_change([pt(0)]))

    def test_zero_baseline_oi_is_none(self):
        self.assertIsNone(signals.oi_change([pt(0, oi=0), pt(15, oi=500)]))


class VolumeSpikeTests(SimpleTestCase):

    def series(self, volumes):
        return [pt(i * 5, volume=v) for i, v in enumerate(volumes)]

    def test_ratio_against_median_of_earlier_intervals(self):
        # intervals: 100,100,100,100,100,300
        result = signals.volume_spike(self.series([0, 100, 200, 300, 400, 500, 800]))
        self.assertEqual(result["ratio"], 3.0)
        self.assertEqual(result["latest_interval_volume"], 300)

    def test_too_little_history_is_none(self):
        self.assertIsNone(signals.volume_spike(self.series([0, 100, 200, 300])))

    def test_volume_reset_restarts_the_history(self):
        points = self.series([0, 100, 200, 300, 400, 500, 50, 150])
        self.assertIsNone(signals.volume_spike(points))

    def test_a_new_day_restarts_the_history(self):
        points = self.series([0, 100, 200, 300, 400, 500, 600])
        points[-1]["t"] += timedelta(days=1)
        self.assertIsNone(signals.volume_spike(points))

    def test_flat_history_is_none_not_infinite(self):
        self.assertIsNone(signals.volume_spike(self.series([0, 0, 0, 0, 0, 0, 100])))


class SpreadTests(SimpleTestCase):

    def test_tightening_is_reported(self):
        points = [pt(0, bid=98, ask=102), pt(15, bid=99.5, ask=100.5)]
        result = signals.spread_tightening(points)
        self.assertTrue(result["tightening"])
        self.assertAlmostEqual(result["spread_pct_before"], 4.0, places=2)
        self.assertAlmostEqual(result["spread_pct_now"], 1.0, places=2)
        self.assertEqual(result["change_pct"], -75.0)

    def test_widening_is_not_tightening(self):
        points = [pt(0, bid=99.5, ask=100.5), pt(15, bid=98, ask=102)]
        self.assertFalse(signals.spread_tightening(points)["tightening"])

    def test_missing_or_crossed_quotes_are_none(self):
        self.assertIsNone(
            signals.spread_tightening([pt(0), pt(15, bid=None, ask=None)])
        )
        self.assertIsNone(signals.spread_tightening([pt(0), pt(15, bid=101, ask=99)]))
        self.assertIsNone(signals.spread_tightening([pt(0, bid=0), pt(15)]))


class IvVelocityTests(SimpleTestCase):

    def test_rising_iv(self):
        series = [{"t": T0, "iv": 14.0}, {"t": T0 + timedelta(minutes=15), "iv": 15.5}]
        result = signals.iv_velocity(series)
        self.assertEqual(result["change_per_window"], 1.5)

    def test_scales_to_the_window(self):
        series = [{"t": T0, "iv": 14.0}, {"t": T0 + timedelta(minutes=10), "iv": 15.0}]
        self.assertEqual(
            signals.iv_velocity(series, window_minutes=10)["change_per_window"], 1.0
        )

    def test_no_baseline_is_none(self):
        self.assertIsNone(signals.iv_velocity([{"t": T0, "iv": 14.0}]))


EXPIRY = date(2026, 10, 8)
SPOT = 24100.0


class ComputeTests(TestCase):
    """Snapshots priced from known volatilities, so the answers are known."""

    @classmethod
    def setUpTestData(cls):
        cls.options = {}
        token = 5000
        for strike in range(23900, 24400, 100):
            for side in ("CE", "PE"):
                token += 1
                cls.options[(strike, side)] = Instrument.objects.create(
                    instrument_token=token,
                    exchange="NFO",
                    symbol="NIFTY",
                    trading_symbol=f"NIFTY{strike}{side}",
                    instrument_type=side,
                    option_type=side,
                    strike=strike,
                    expiry=EXPIRY,
                )

    def snapshot(self, at, vol, oi_ce=1000, volume=0):
        t = signals._years_to_expiry(EXPIRY, at)
        forward = SPOT * 1.0005
        for (strike, side), instrument in self.options.items():
            ltp = black76.price(forward, strike, t, signals.RISK_FREE_RATE, vol, side)
            OptionSnapshot.objects.create(
                underlying="NIFTY",
                instrument=instrument,
                captured_at=at,
                spot=SPOT,
                ltp=round(ltp, 2),
                bid=round(ltp - 0.5, 2),
                ask=round(ltp + 0.5, 2),
                volume=volume,
                oi=oi_ce if side == "CE" else 2000,
            )

    def test_empty_history_is_all_not_evaluable(self):
        result = SnapshotSignalsService.compute("NIFTY", now=T0)
        self.assertEqual(result["snapshots"], 0)
        self.assertIsNone(result["iv_velocity"])
        self.assertEqual(result["oi_change"], {"CE": None, "PE": None})

    def test_iv_velocity_and_oi_change_from_stored_snapshots(self):
        self.snapshot(T0, vol=0.14, oi_ce=1000)
        self.snapshot(T0 + timedelta(minutes=5), vol=0.145, oi_ce=1050)
        self.snapshot(T0 + timedelta(minutes=10), vol=0.15, oi_ce=1100)
        self.snapshot(T0 + timedelta(minutes=15), vol=0.155, oi_ce=1200)

        result = SnapshotSignalsService.compute("NIFTY", now=T0 + timedelta(minutes=16))

        self.assertEqual(result["atm_strike"], 24100.0)
        self.assertEqual(result["snapshots"], 4)
        self.assertAlmostEqual(
            result["iv_velocity"]["change_per_window"], 1.5, delta=0.1
        )
        self.assertEqual(result["oi_change"]["CE"]["change"], 200)
        self.assertEqual(result["oi_change"]["PE"]["change"], 0)
        self.assertIsNone(result["volume_spike"]["CE"])  # too little history

    def test_stale_latest_snapshot_makes_everything_not_evaluable(self):
        self.snapshot(T0, vol=0.14)
        self.snapshot(T0 + timedelta(minutes=15), vol=0.15)

        result = SnapshotSignalsService.compute("NIFTY", now=T0 + timedelta(minutes=45))

        self.assertEqual(result["snapshots"], 2)
        self.assertIsNone(result["iv_velocity"])
        self.assertEqual(result["oi_change"], {"CE": None, "PE": None})
