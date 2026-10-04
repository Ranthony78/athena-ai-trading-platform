"""Daily pivots/CPR come from the previous completed session, not the previous candle."""

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, TestCase

from .indicators.pivot import CPR, PivotPoints
from .models import Candle, Instrument
from .services.daily_levels_service import DailyLevelsService

IST = ZoneInfo("Asia/Kolkata")

# Bank Nifty, 1 Oct session, as printed in the analysis report.
HIGH, LOW, CLOSE = 55091.45, 54066.60, 54450.75


class PivotFormulaTests(SimpleTestCase):

    def test_classic_pivots_match_the_reference_report(self):
        levels = PivotPoints.from_prior_session(HIGH, LOW, CLOSE)
        self.assertAlmostEqual(levels["pp"], 54536.27, places=1)
        self.assertAlmostEqual(levels["r1"], 55005.93, places=1)
        self.assertAlmostEqual(levels["s1"], 53981.10, places=1)
        self.assertAlmostEqual(levels["r2"], 55561.12, places=1)
        self.assertAlmostEqual(levels["s2"], 53511.42, places=1)

    def test_cpr_is_ordered_and_centred_on_the_pivot(self):
        cpr = CPR.from_prior_session(HIGH, LOW, CLOSE)
        self.assertAlmostEqual(cpr["bc"], 54579.03, places=1)
        self.assertAlmostEqual(cpr["pp"], 54536.27, places=1)
        self.assertAlmostEqual(cpr["tc"], 54493.52, places=1)
        self.assertAlmostEqual(cpr["width"], abs(cpr["tc"] - cpr["bc"]), places=6)


class PreviousSessionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.instrument = Instrument.objects.create(
            instrument_token=260105,
            exchange="NSE",
            symbol="BANKNIFTY",
            trading_symbol="NIFTY BANK",
            instrument_type="IDX",
        )

    def add_day(self, day, high, low, close):
        Candle.objects.create(
            instrument=self.instrument,
            timeframe="1d",
            candle_time=datetime(day.year, day.month, day.day, 0, 0, tzinfo=IST),
            open=Decimal(str(close)),
            high=Decimal(str(high)),
            low=Decimal(str(low)),
            close=Decimal(str(close)),
        )

    def test_uses_the_latest_completed_day_before_the_session(self):
        self.add_day(date(2026, 9, 30), 54900, 54000, 54300)
        self.add_day(date(2026, 10, 1), HIGH, LOW, CLOSE)
        self.add_day(date(2026, 10, 2), 55200, 54400, 55000)

        result = DailyLevelsService.levels("BANKNIFTY", session_date=date(2026, 10, 2))

        self.assertEqual(result["based_on"]["date"], "2026-10-01")
        self.assertAlmostEqual(result["pivot"]["pp"], 54536.27, places=1)

    def test_todays_incomplete_candle_is_never_used(self):
        self.add_day(date(2026, 10, 2), 55200, 54400, 55000)

        self.assertIsNone(
            DailyLevelsService.levels("BANKNIFTY", session_date=date(2026, 10, 2))
        )

    def test_no_daily_candles_gives_none_not_a_guess(self):
        self.assertIsNone(
            DailyLevelsService.levels("BANKNIFTY", session_date=date(2026, 10, 2))
        )

    def test_unknown_symbol_gives_none(self):
        self.assertIsNone(
            DailyLevelsService.levels("NOSUCH", session_date=date(2026, 10, 2))
        )

    def test_corrupt_candle_gives_none(self):
        self.add_day(date(2026, 10, 1), 100, 200, 150)  # high below low

        self.assertIsNone(
            DailyLevelsService.levels("BANKNIFTY", session_date=date(2026, 10, 2))
        )

    # A months-old daily candle must not pass as the previous session.
    def test_candle_older_than_a_week_gives_none(self):
        self.add_day(date(2026, 8, 7), HIGH, LOW, CLOSE)

        self.assertIsNone(
            DailyLevelsService.levels("BANKNIFTY", session_date=date(2026, 10, 5))
        )

    def test_a_long_weekend_still_counts(self):
        self.add_day(date(2026, 10, 1), HIGH, LOW, CLOSE)

        result = DailyLevelsService.levels("BANKNIFTY", session_date=date(2026, 10, 6))
        self.assertEqual(result["based_on"]["date"], "2026-10-01")
