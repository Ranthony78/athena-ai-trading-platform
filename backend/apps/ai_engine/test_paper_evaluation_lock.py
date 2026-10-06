from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_engine.models import AnalysisSession
from apps.ai_engine.services.paper_evaluation_service import PaperEvaluationService


class PaperEvaluationLockTests(TestCase):
    """
    Runs the real row-locking query. On PostgreSQL (the CI PostgreSQL job)
    FOR UPDATE across the nullable user join raised NotSupportedError, so
    every scheduled paper evaluation was skipped; SQLite ignores the lock.
    """

    def test_start_runs_its_locking_query(self):
        user = get_user_model().objects.create_user("u", "u@example.com", "x")
        session = AnalysisSession.objects.create(
            user=user,
            session_type="MARKET_ANALYSIS",
            status="COMPLETE",
            parsed_output={"signal": "NO_SETUP"},
            paper_evaluation={"status": "REQUESTED"},
        )
        result = PaperEvaluationService.start(session.id)
        self.assertEqual(result["status"], "SKIPPED")
        self.assertNotIn("unavailable", result["reason"].lower())
