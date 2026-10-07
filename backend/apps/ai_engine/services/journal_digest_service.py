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

        resolved = [s for s in sessions if s.forecast_outcome_status == "RESOLVED"]
        # Failed runs are not analyses, but hiding them makes the day look quieter
        # than it was (7 Oct: 4 of 8 runs timed out and the draft said "4 runs").
        failed = list(
            AnalysisSession.objects.filter(
                user=user, created_at__date=today, status="FAILED"
            )
            .select_related("instrument")
            .order_by("created_at")
        )
        if not sessions and not failed:
            return "skipped (no AI runs today)"
        notes = [
            "Automatic draft from today's saved AI runs. Review before relying on it.",
            "",
            *(cls._line(s) for s in sessions),
            "",
            f"{len(sessions)} runs, {len(resolved)} forecasts resolved so far.",
        ]
        if failed:
            notes += ["", f"{len(failed)} runs failed and are not counted above:"]
            notes += [
                f"{timezone.localtime(s.created_at):%H:%M} "
                f"{s.instrument.symbol if s.instrument else '?'}: "
                f"{(s.error_message or 'no reason recorded')[:120]}"
                for s in failed
            ]
        JournalEntry.objects.create(
            user=user,
            date=today,
            session=DIGEST_SESSION,
            title=f"{DIGEST_TITLE_PREFIX} - {today:%d %b %Y}",
            market_notes="\n".join(notes),
        )
        return f"saved draft with {len(sessions)} runs"
