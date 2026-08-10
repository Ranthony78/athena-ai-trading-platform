import logging

from celery import shared_task

logger = logging.getLogger(__name__)

# Symbols Athena actually trades — no reason to sync intraday candles for
# anything else on a recurring schedule.
INTRADAY_SYNC_SYMBOLS = ["NIFTY", "BANKNIFTY"]
INTRADAY_SYNC_TIMEFRAMES = ["5m", "15m"]

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
def sync_intraday_candles():
    """
    Scheduled task: keep today's intraday candles current during market
    hours. Without this, SessionStructureService, multi-timeframe trend,
    and primary-timeframe indicators would all be reading stale or
    missing data once the market's actually open — this task exists to
    close that gap, following the exact same market-hours-check pattern
    as track_signal_outcomes.
    """
    from datetime import date

    from django.contrib.auth import get_user_model

    from .engine.market_state import MarketState
    from .services.candle_service import CandleService
    from apps.zerodha.repositories.zerodha_repository import ZerodhaConfigRepository

    session = MarketState.session_info()
    if not session["is_live"]:
        logger.info("Market closed — skipping intraday candle sync.")
        return "skipped (market closed)"

    config = ZerodhaConfigRepository.model.objects.filter(is_connected=True).first()
    if not config or not config.is_token_valid:
        logger.warning("No user with a valid Zerodha connection — skipping intraday candle sync.")
        return "skipped (no valid Zerodha connection)"

    user = config.user
    today_str = date.today().isoformat()
    service = CandleService(user=user)
    results = {}

    for symbol in INTRADAY_SYNC_SYMBOLS:
        for timeframe in INTRADAY_SYNC_TIMEFRAMES:
            try:
                count = service.fetch_and_store(
                    symbol=symbol,
                    timeframe=timeframe,
                    from_date=today_str,
                    to_date=today_str,
                )
                results[f"{symbol}_{timeframe}"] = count
            except Exception as e:
                logger.error(f"sync_intraday_candles failed [{symbol} {timeframe}]: {e}")
                results[f"{symbol}_{timeframe}"] = f"error: {e}"

    logger.info(f"Intraday candle sync run: {results}")
    return results

@shared_task
def ping():
    """Trivial task to confirm Celery is wired up correctly."""
    logger.info("Celery ping task executed successfully.")
    return "pong"