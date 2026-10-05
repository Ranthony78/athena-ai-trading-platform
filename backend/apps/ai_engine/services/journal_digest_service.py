import logging

from django.utils import timezone

logger = logging.getLogger(__name__)

DIGEST_SESSION = "POST_MARKET"
DIGEST_TITLE_PREFIX = "[Auto draft] AI forward test"


class JournalDigestService:
    """
    Writes ONE draft journal entry per day listing the AI runs and how their
    forecasts turned out. It never edits an existing entry, never rates the
    day, and never touches the user's own entries.
    """

    @staticmethod
    def _line(session) -> str:
        local = timezone.localtime(session.created_at)
        out = session.parsed_output or {}
        mode = (session.market_context or {}).get("analysis_mode", "LIVE")
        symbol = session.instrument.symbol if session.instrument else "?"
        forecast = session.forecast_outcome_status
        if session.forecast_actual_class:
            forecast = f"{forecast} - price went {session.forecast_actual_class}"
        paper = (session.paper_evaluation or {}).get("status", "OFF")
        return (
            f"{local:%H:%M} {symbol} [{mode}] signal {out.get('signal', '-')}, "
            f"confidence {out.get('confidence_level', '-')} | "
            f"forecast: {forecast} | paper: {paper}"
        )

    @classmethod
    def write_for_today(cls, user) -> str:
        from apps.journal.models import JournalEntry

        from ..models import AnalysisSession

        today = timezone.localdate()
        if today.weekday() >= 5:
            return "skipped (weekend)"
        if JournalEntry.objects.filter(
            user=user, date=today, session=DIGEST_SESSION
        ).exists():
            return "skipped (draft already exists)"
        sessions = list(
            AnalysisSession.objects.filter(
                user=user, created_at__date=today, status="COMPLETE"
            )
            .select_related("instrument")
            .order_by("created_at")
        )
        if not sessions:
            return "skipped (no AI runs today)"

        resolved = [s for s in sessions if s.forecast_outcome_status == "RESOLVED"]
        notes = [
            "Automatic draft from today's saved AI runs. Review before relying on it.",
            "",
            *(cls._line(s) for s in sessions),
            "",
            f"{len(sessions)} runs, {len(resolved)} forecasts resolved so far.",
        ]
        JournalEntry.objects.create(
            user=user,
            date=today,
            session=DIGEST_SESSION,
            title=f"{DIGEST_TITLE_PREFIX} - {today:%d %b %Y}",
            market_notes="\n".join(notes),
        )
        return f"saved draft with {len(sessions)} runs"
