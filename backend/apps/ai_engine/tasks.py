import logging

from celery import shared_task

logger = logging.getLogger(__name__)

# Symbols analysed each evening. One saved run per symbol per day at most.
SCHEDULED_SYMBOLS = ["NIFTY", "BANKNIFTY"]
SCHEDULED_HORIZON_MINUTES = 30


def _pick_user():
    """The user whose saved Zerodha session and AI key the scheduled run may use."""
    from apps.zerodha.repositories.zerodha_repository import ZerodhaConfigRepository

    config = ZerodhaConfigRepository.model.objects.filter(is_connected=True).first()
    if not config or not config.is_token_valid:
        return None
    return config.user


@shared_task
def run_scheduled_next_session_analysis():
    """
    Evening task: save a NEXT_SESSION outlook for each index so it can be
    compared with the real next day (see `manage.py forecast_vs_actual`).

    Guards, in order: weekdays only; a daily candle for today must exist
    (stands in for "was a trading day" - there is no holiday calendar); a
    valid Zerodha session; and no run already saved today for that symbol,
    so a retry or a second beat never spends AI quota twice.
    """
    from django.utils import timezone

    from apps.market_data.models import Candle

    from .models import AnalysisSession
    from .services.analysis_service import AnalysisService

    today = timezone.localdate()
    if today.weekday() >= 5:
        return "skipped (weekend)"

    user = _pick_user()
    if user is None:
        logger.warning("Scheduled analysis skipped: no valid Zerodha connection.")
        return "skipped (no valid Zerodha connection)"

    # The intraday sync does not store the day's daily candle, so fetch it now.
    # It is the basis of the next-session outlook and of the trading-day guard.
    from apps.market_data.services.candle_service import CandleService

    candles = CandleService(user=user)
    results = {}
    for symbol in SCHEDULED_SYMBOLS:
        try:
            candles.fetch_and_store(
                symbol=symbol,
                timeframe="1d",
                from_date=today.isoformat(),
                to_date=today.isoformat(),
            )
        except Exception as e:
            logger.error(f"Daily candle fetch failed [{symbol}]: {type(e).__name__}")
        has_today = Candle.objects.filter(
            instrument__symbol__in=[symbol, f"{symbol} 50"],
            timeframe="1d",
            candle_time__date=today,
        ).exists()
        if not has_today:
            results[symbol] = "skipped (no daily candle for today; holiday or data gap)"
            continue
        already = AnalysisSession.objects.filter(
            instrument__symbol__in=[symbol, f"{symbol} 50"],
            created_at__date=today,
            market_context__analysis_mode="NEXT_SESSION",
            status="COMPLETE",
        ).exists()
        if already:
            results[symbol] = "skipped (already saved today)"
            continue
        try:
            out = AnalysisService(user=user).analyze(
                symbol=symbol,
                timeframe="15m",
                session_type="MARKET_ANALYSIS",
                persist=True,
                forecast_horizon_minutes=SCHEDULED_HORIZON_MINUTES,
                paper_evaluate=False,
                analysis_mode="NEXT_SESSION",
            )
            results[symbol] = f"saved session {out.get('session_id')}"
        except Exception as e:
            logger.error(f"Scheduled analysis failed [{symbol}]: {type(e).__name__}")
            results[symbol] = f"error: {type(e).__name__}"

    logger.info(f"Scheduled next-session analysis: {results}")
    return results
