from datetime import date, datetime
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.ai_engine import tasks
from apps.ai_engine.models import AnalysisSession
from apps.market_data.models import Candle, Instrument

FRIDAY = date(2026, 10, 2)
SATURDAY = date(2026, 10, 3)


def _aware(day, hour=0):
    return timezone.make_aware(datetime(day.year, day.month, day.day, hour))


class ScheduledAnalysisTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("u", "u@example.com", "x")
        self.nifty = Instrument.objects.create(
            instrument_token=1,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )
        self.bank = Instrument.objects.create(
            instrument_token=2,
            exchange="NSE",
            symbol="BANKNIFTY 50",
            trading_symbol="NIFTY BANK",
            instrument_type="IDX",
        )

    def _candle(self, instrument, day):
        Candle.objects.create(
            instrument=instrument,
            timeframe="1d",
            candle_time=_aware(day),
            open=100,
            high=101,
            low=99,
            close=100,
        )

    def _run(self, today, user="default"):
        user = self.user if user == "default" else user
        with (
            mock.patch("django.utils.timezone.localdate", return_value=today),
            mock.patch.object(tasks, "_pick_user", return_value=user),
            mock.patch("apps.market_data.services.candle_service.CandleService"),
            mock.patch(
                "apps.ai_engine.services.analysis_service.AnalysisService"
            ) as svc,
        ):
            svc.return_value.analyze.return_value = {"session_id": 7}
            result = tasks.run_scheduled_next_session_analysis()
        return result, svc

    def test_weekend_is_skipped(self):
        result, svc = self._run(SATURDAY)
        self.assertEqual(result, "skipped (weekend)")
        svc.return_value.analyze.assert_not_called()

    def test_no_zerodha_session_is_skipped(self):
        result, svc = self._run(FRIDAY, user=None)
        self.assertIn("no valid Zerodha", result)
        svc.return_value.analyze.assert_not_called()

    def test_no_daily_candle_means_no_run(self):
        result, svc = self._run(FRIDAY)
        self.assertIn("no daily candle", result["NIFTY"])
        svc.return_value.analyze.assert_not_called()

    def test_runs_next_session_for_both_indices(self):
        self._candle(self.nifty, FRIDAY)
        self._candle(self.bank, FRIDAY)
        result, svc = self._run(FRIDAY)
        self.assertEqual(result["NIFTY"], "saved session 7")
        self.assertEqual(svc.return_value.analyze.call_count, 2)
        kwargs = svc.return_value.analyze.call_args.kwargs
        self.assertEqual(kwargs["analysis_mode"], "NEXT_SESSION")
        self.assertFalse(kwargs["paper_evaluate"])

    def test_second_run_the_same_day_spends_nothing(self):
        # A session saved "now" is dated with the real today, so run as that
        # day (a weekday is needed; on weekends pretend it is the last Friday).
        real_today = timezone.localdate()
        if real_today.weekday() >= 5:
            self.skipTest("needs a weekday to date the saved session")
        for inst in (self.nifty, self.bank):
            self._candle(inst, real_today)
        AnalysisSession.objects.create(
            instrument=self.nifty,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            market_context={"analysis_mode": "NEXT_SESSION"},
        )
        result, svc = self._run(real_today)
        self.assertEqual(result["NIFTY"], "skipped (already saved today)")
        self.assertEqual(result["BANKNIFTY"], "saved session 7")
        self.assertEqual(svc.return_value.analyze.call_count, 1)


class ForecastVsActualCommandTests(TestCase):
    def test_no_outlooks_is_reported_plainly(self):
        out = StringIO()
        call_command("forecast_vs_actual", stdout=out)
        self.assertIn("No saved next-session outlooks", out.getvalue())

    def test_pending_then_actual(self):
        inst = Instrument.objects.create(
            instrument_token=9,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )
        AnalysisSession.objects.create(
            instrument=inst,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            market_context={"analysis_mode": "NEXT_SESSION"},
            parsed_output={"signal": "NO_SETUP", "confidence_level": "LOW"},
        )
        out = StringIO()
        call_command("forecast_vs_actual", stdout=out)
        self.assertIn("pending", out.getvalue())
