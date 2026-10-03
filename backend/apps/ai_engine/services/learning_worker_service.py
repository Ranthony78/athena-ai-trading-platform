"""Bounded recurring evaluation; safe to invoke from Celery or the local runner."""

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from ..models import AnalysisSession, LearningWorkerState
from .forecast_outcome_service import ForecastOutcomeService
from .paper_evaluation_service import PaperEvaluationService

logger = logging.getLogger(__name__)


class LearningWorkerService:
    @staticmethod
    def tick():
        now = timezone.now()
        LearningWorkerState.objects.get_or_create(name="default")
        # Database lease serializes local and Celery workers, including on SQLite.
        acquired = (
            LearningWorkerState.objects.filter(name="default")
            .filter(
                Q(lease_until__isnull=True) | Q(lease_until__lt=now),
            )
            .update(lease_until=now + timedelta(minutes=10))
        )
        if not acquired:
            return {"status": "another_worker_running"}
        result = {
            "status": "complete",
            "paper_checked": 0,
            "errors": 0,
            "candle_syncs": 0,
        }
        try:
            # Exits have priority. There are no AI calls or live-order methods here.
            for session in (
                AnalysisSession.objects.filter(
                    status="COMPLETE", forecast_target_time__lte=now
                )
                .exclude(paper_evaluation={})
                .iterator()
            ):
                if (session.paper_evaluation or {}).get("status") in (
                    "OPEN",
                    "WAITING_EXIT",
                    "PARTIAL_EXIT",
                ):
                    try:
                        PaperEvaluationService.close_due(session.id)
                        result["paper_checked"] += 1
                    except Exception as exc:
                        result["errors"] += 1
                        logger.warning(
                            "Paper evaluation deferred (%s)", type(exc).__name__
                        )
            # Fetch real one-minute candles for due predictions, also after close.
            # Data is shared by instrument, but credentials remain user scoped.
            from apps.market_data.services.candle_service import CandleService

            due = AnalysisSession.objects.filter(
                status="COMPLETE",
                forecast_outcome_status="PENDING",
                forecast_target_time__lte=now - timedelta(minutes=1),
                forecast_target_time__date=timezone.localdate(),
                user__isnull=False,
                instrument__isnull=False,
            ).select_related("user", "instrument")
            seen = set()
            for session in due[:100]:
                date = timezone.localdate(session.forecast_target_time).isoformat()
                key = (session.user_id, session.instrument.symbol, date)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    service = CandleService(user=session.user)
                    if getattr(service.provider, "data_source", "UNKNOWN") == "ZERODHA":
                        service.fetch_and_store(
                            session.instrument.symbol, "1m", date, date
                        )
                        result["candle_syncs"] += 1
                except Exception as exc:
                    result["errors"] += 1
                    logger.warning(
                        "Forecast candle refresh unavailable (%s)", type(exc).__name__
                    )
            result["forecasts"] = ForecastOutcomeService.resolve_due_forecasts()
            return result
        except Exception:
            result["status"] = "error"
            raise
        finally:
            LearningWorkerState.objects.filter(name="default").update(
                heartbeat_at=timezone.now() if result["status"] == "complete" else None,
                result=result,
                lease_until=None,
            )
