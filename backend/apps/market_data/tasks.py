import logging

from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def track_signal_outcomes():
    """Scheduled task: check all OPEN signals against real prices."""
    from .engine.market_state import MarketState
    from .services.outcome_tracking_service import OutcomeTrackingService

    session = MarketState.session_info()
    if not session["is_live"]:
        logger.info("Market closed — skipping outcome tracking run.")
        return "skipped (market closed)"

    result = OutcomeTrackingService.track_all_open_signals()
    logger.info(f"Outcome tracking run: {result}")
    return result

@shared_task
def ping():
    """Trivial task to confirm Celery is wired up correctly."""
    logger.info("Celery ping task executed successfully.")
    return "pong"