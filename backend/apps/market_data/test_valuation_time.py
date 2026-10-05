from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from apps.market_data.services.option_chain_service import OptionChainService
from apps.market_data.services.snapshot_signals_service import valuation_time

IST = ZoneInfo("Asia/Kolkata")
HOUR = 1 / (365 * 24)


def ist(*args):
    return datetime(*args, tzinfo=IST)


class ValuationTimeTests(SimpleTestCase):
    def test_live_quote_uses_its_own_time(self):
        now = ist(2026, 10, 6, 9, 31)
        self.assertEqual(
            valuation_time("2026-10-06T09:30:00", now), ist(2026, 10, 6, 9, 30)
        )

    def test_after_hours_quote_is_capped_at_the_close(self):
        # Kite stamps 17:35 but the prices are the 15:30 closing prices.
        now = ist(2026, 10, 6, 2, 3)
        self.assertEqual(
            valuation_time("2026-10-05 17:35:05", now), ist(2026, 10, 5, 15, 30)
        )

    def test_bad_or_future_timestamps_fall_back_to_now(self):
        now = ist(2026, 10, 6, 10, 0)
        self.assertEqual(valuation_time(None, now), now)
        self.assertEqual(valuation_time("not a time", now), now)
        self.assertEqual(valuation_time("2026-10-06T11:00:00", now), now)


class ChainTimeToExpiryTests(SimpleTestCase):
    def test_expiry_morning_counts_the_real_hours_left(self):
        t = OptionChainService._time_to_expiry_years(
            "2026-10-06", at=ist(2026, 10, 6, 9, 30)
        )
        self.assertAlmostEqual(t / HOUR, 6.0, places=3)  # 09:30 -> 15:30

    def test_night_before_expiry_values_the_close_with_a_day_left(self):
        # The bug: at 02:03 on expiry day whole-day counting gave 0 days
        # (floored to 1 hour) for prices that were set at 15:30 the day before.
        at = valuation_time("2026-10-05 17:35:05", ist(2026, 10, 6, 2, 3))
        t = OptionChainService._time_to_expiry_years("2026-10-06", at=at)
        self.assertAlmostEqual(t / HOUR, 24.0, places=3)

    def test_after_expiry_close_is_floored_at_one_hour(self):
        t = OptionChainService._time_to_expiry_years(
            "2026-10-06", at=ist(2026, 10, 6, 16, 0)
        )
        self.assertAlmostEqual(t / HOUR, 1.0, places=6)

    def test_expiry_a_week_out(self):
        t = OptionChainService._time_to_expiry_years(
            str(date(2026, 10, 13)), at=ist(2026, 10, 6, 15, 30)
        )
        self.assertAlmostEqual(t / HOUR, 7 * 24, places=3)
