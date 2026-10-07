from datetime import date, datetime, timedelta
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
            symbol="NIFTY BANK",
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


class LiveScheduleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("u", "u@example.com", "x")
        self.nifty = Instrument.objects.create(
            instrument_token=11,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )

    def _run(self, live=True, weekday=True, user="default"):
        user = self.user if user == "default" else user
        day = FRIDAY if weekday else SATURDAY
        with (
            mock.patch("django.utils.timezone.localdate", return_value=day),
            mock.patch(
                "apps.market_data.engine.market_state.MarketState.session_info",
                return_value={"is_live": live},
            ),
            mock.patch.object(tasks, "_pick_user", return_value=user),
            mock.patch(
                "apps.ai_engine.services.analysis_service.AnalysisService"
            ) as svc,
        ):
            svc.return_value.analyze.return_value = {"session_id": 5}
            result = tasks.run_scheduled_live_analysis()
        return result, svc

    def test_skips_when_market_closed_weekend_or_no_zerodha(self):
        self.assertEqual(self._run(live=False)[0], "skipped (market closed)")
        self.assertEqual(self._run(weekday=False)[0], "skipped (weekend)")
        self.assertIn("no valid Zerodha", self._run(user=None)[0])

    def test_runs_live_with_paper_evaluation_for_both_indices(self):
        result, svc = self._run()
        self.assertEqual(svc.return_value.analyze.call_count, 2)
        kwargs = svc.return_value.analyze.call_args.kwargs
        self.assertEqual(kwargs["analysis_mode"], "LIVE")
        self.assertTrue(kwargs["paper_evaluate"])
        self.assertEqual(result["NIFTY"], "saved session 5")

    def test_daily_cap_stops_further_runs(self):
        # created_at is auto-set to the real now, so run as the real today.
        real_today = timezone.localdate()
        if real_today.weekday() >= 5:
            self.skipTest("needs a weekday")
        for _ in range(tasks.DAILY_ANALYSIS_CAP):
            AnalysisSession.objects.create(
                instrument=self.nifty,
                user=self.user,
                session_type="MARKET_ANALYSIS",
                status="COMPLETE",
            )
        with (
            mock.patch(
                "apps.market_data.engine.market_state.MarketState.session_info",
                return_value={"is_live": True},
            ),
            mock.patch.object(tasks, "_pick_user", return_value=self.user),
            mock.patch(
                "apps.ai_engine.services.analysis_service.AnalysisService"
            ) as svc,
        ):
            result = tasks.run_scheduled_live_analysis()
        self.assertIn("daily cap", result["NIFTY"])
        svc.return_value.analyze.assert_not_called()

    def test_recent_live_run_is_not_repeated(self):
        real_today = timezone.localdate()
        if real_today.weekday() >= 5:
            self.skipTest("needs a weekday")
        AnalysisSession.objects.create(
            instrument=self.nifty,
            user=self.user,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            market_context={"analysis_mode": "LIVE"},
        )
        with (
            mock.patch(
                "apps.market_data.engine.market_state.MarketState.session_info",
                return_value={"is_live": True},
            ),
            mock.patch.object(tasks, "_pick_user", return_value=self.user),
            mock.patch(
                "apps.ai_engine.services.analysis_service.AnalysisService"
            ) as svc,
        ):
            result = tasks.run_scheduled_live_analysis()
        self.assertIn("in the last 20 minutes", result["NIFTY"])
        self.assertEqual(svc.return_value.analyze.call_count, 1)  # BANKNIFTY only


class LiveScheduleManualRunTests(TestCase):
    """A manual run 30 minutes before a slot must not cancel the slot."""

    def setUp(self):
        self.user = get_user_model().objects.create_user("u", "u@example.com", "x")
        self.nifty = Instrument.objects.create(
            instrument_token=31,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )

    def test_earlier_manual_run_does_not_block_the_slot(self):
        if timezone.localdate().weekday() >= 5:
            self.skipTest("needs a weekday")
        manual = AnalysisSession.objects.create(
            instrument=self.nifty,
            user=self.user,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            market_context={"analysis_mode": "LIVE"},
        )
        AnalysisSession.objects.filter(pk=manual.pk).update(
            created_at=timezone.now() - timedelta(minutes=30)
        )
        with (
            mock.patch(
                "apps.market_data.engine.market_state.MarketState.session_info",
                return_value={"is_live": True},
            ),
            mock.patch.object(tasks, "_pick_user", return_value=self.user),
            mock.patch(
                "apps.ai_engine.services.analysis_service.AnalysisService"
            ) as svc,
        ):
            svc.return_value.analyze.return_value = {"session_id": 9}
            result = tasks.run_scheduled_live_analysis()
        self.assertEqual(result["NIFTY"], "saved session 9")


class JournalDigestTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("u", "u@example.com", "x")
        self.nifty = Instrument.objects.create(
            instrument_token=21,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )

    def _session(self):
        return AnalysisSession.objects.create(
            instrument=self.nifty,
            user=self.user,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            market_context={"analysis_mode": "LIVE"},
            parsed_output={"signal": "NO_SETUP", "confidence_level": "LOW"},
            forecast_outcome_status="RESOLVED",
            forecast_actual_class="SIDEWAYS",
        )

    def test_writes_one_draft_and_never_overwrites(self):
        from apps.ai_engine.services.journal_digest_service import JournalDigestService
        from apps.journal.models import JournalEntry

        if timezone.localdate().weekday() >= 5:
            self.skipTest("needs a weekday")
        self._session()
        self.assertIn("saved draft", JournalDigestService.write_for_today(self.user))
        entry = JournalEntry.objects.get(user=self.user)
        self.assertIn("NO_SETUP", entry.market_notes)
        self.assertEqual(entry.rating, 0)  # never rates the day
        entry.market_notes = "my edits"
        entry.save()
        self.assertIn("already exists", JournalDigestService.write_for_today(self.user))
        entry.refresh_from_db()
        self.assertEqual(entry.market_notes, "my edits")

    def test_failed_runs_are_listed_not_hidden(self):
        from apps.ai_engine.services.journal_digest_service import JournalDigestService
        from apps.journal.models import JournalEntry

        if timezone.localdate().weekday() >= 5:
            self.skipTest("needs a weekday")
        self._session()
        AnalysisSession.objects.create(
            instrument=self.nifty,
            user=self.user,
            session_type="MARKET_ANALYSIS",
            status="FAILED",
            error_message="Gemini did not respond before the request timed out.",
        )
        JournalDigestService.write_for_today(self.user)
        notes = JournalEntry.objects.get(user=self.user).market_notes
        self.assertIn("1 runs failed", notes)
        self.assertIn("timed out", notes)

    def test_no_runs_means_no_draft(self):
        from apps.ai_engine.services.journal_digest_service import JournalDigestService

        if timezone.localdate().weekday() >= 5:
            self.skipTest("needs a weekday")
        self.assertIn("no AI runs", JournalDigestService.write_for_today(self.user))
