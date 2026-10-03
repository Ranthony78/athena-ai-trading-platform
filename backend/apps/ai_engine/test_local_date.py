"""
Regression: "today's sessions / signals" must use the local (Asia/Kolkata) date.

session_time__date and signal_time__date are evaluated by the database in the
local timezone, but "today" was taken from the UTC date, so between 00:00 and
05:30 IST the AI Workspace "today" lists looked at yesterday.
"""

from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.market_data.models import Instrument

from .models import AISignal, AnalysisSession
from .repositories.ai_repository import AISignalRepository, AnalysisSessionRepository

User = get_user_model()

# 2026-10-03 20:30 UTC is 2026-10-04 02:00 IST.
NIGHT = datetime(2026, 10, 3, 20, 30, tzinfo=dt_timezone.utc)
EARLIER = datetime(2026, 10, 3, 9, 30, tzinfo=dt_timezone.utc)  # 15:00 IST on the 3rd


@patch("django.utils.timezone.now", return_value=NIGHT)
class AiEngineLocalDateTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("ai", "ai@example.com", "pw-Ai-123456")
        self.instrument = Instrument.objects.create(
            instrument_token=999000042,
            exchange="NSE",
            symbol="NIFTY 50",
            trading_symbol="NIFTY 50",
            instrument_type="IDX",
        )

    def make_session(self, at):
        session = AnalysisSession.objects.create(
            instrument=self.instrument,
            user=self.user,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
        )
        AnalysisSession.objects.filter(pk=session.pk).update(session_time=at)
        return session

    def make_signal(self, at):
        session = self.make_session(at)
        return AISignal.objects.create(
            session=session,
            instrument=self.instrument,
            user=self.user,
            signal="BUY",
            reasoning="test",
            signal_time=at,
        )

    def test_sessions_created_after_local_midnight_count_as_today(self, _now):
        today = self.make_session(NIGHT)
        self.make_session(EARLIER)  # the previous local day

        found = list(AnalysisSessionRepository.get_today(user=self.user))

        self.assertEqual([s.pk for s in found], [today.pk])

    def test_signals_created_after_local_midnight_count_as_today(self, _now):
        today = self.make_signal(NIGHT)
        self.make_signal(EARLIER)

        found = list(AISignalRepository.get_today(user=self.user))

        self.assertEqual([s.pk for s in found], [today.pk])
