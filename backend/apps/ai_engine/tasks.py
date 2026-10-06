import logging

from celery import shared_task

logger = logging.getLogger(__name__)

# Symbols analysed each evening. One saved run per symbol per day at most.
SCHEDULED_SYMBOLS = ["NIFTY", "BANKNIFTY"]
SCHEDULED_HORIZON_MINUTES = 30


def _instrument(symbol):
    """The index instrument Athena itself uses for this code (NIFTY -> NIFTY 50, BANKNIFTY -> NIFTY BANK)."""
    from apps.market_data.repositories.instrument_repository import (
        InstrumentRepository,
    )

    return InstrumentRepository.get_by_symbol(symbol)


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
            instrument=_instrument(symbol),
            timeframe="1d",
            candle_time__date=today,
        ).exists()
        if not has_today:
            results[symbol] = "skipped (no daily candle for today; holiday or data gap)"
            continue
        already = AnalysisSession.objects.filter(
            instrument=_instrument(symbol),
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


# ----------------------------------------------------------------------
# In-market scheduled analysis (forward testing)
# ----------------------------------------------------------------------

# Hard ceiling on analyses saved per day for the scheduled user, manual runs
# included. Stops a bug or a retry loop from burning AI quota.
DAILY_ANALYSIS_CAP = 8
# A LIVE run for the same symbol inside this window means the slot already ran
# (double beat, restart, retry) and is skipped. Short on purpose: a manual run
# half an hour earlier must not cancel the scheduled slot.
DUPLICATE_WINDOW_MINUTES = 20


@shared_task
def run_scheduled_live_analysis():
    """
    Mid-session task (09:30, 11:30, 13:30 IST on weekdays): save a LIVE
    analysis for each index with paper evaluation switched on, so the forecast
    and the simulated paper trade are tracked against what price then did.
    Paper only: no live order is ever placed from here.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.market_data.engine.market_state import MarketState

    from .models import AnalysisSession
    from .services.analysis_service import AnalysisService

    now = timezone.now()
    if timezone.localdate().weekday() >= 5:
        return "skipped (weekend)"
    if not MarketState.session_info()["is_live"]:
        return "skipped (market closed)"
    user = _pick_user()
    if user is None:
        logger.warning("Scheduled live analysis skipped: no valid Zerodha connection.")
        return "skipped (no valid Zerodha connection)"

    results = {}
    for symbol in SCHEDULED_SYMBOLS:
        used_today = AnalysisSession.objects.filter(
            user=user, created_at__date=timezone.localdate()
        ).count()
        if used_today >= DAILY_ANALYSIS_CAP:
            results[symbol] = f"skipped (daily cap of {DAILY_ANALYSIS_CAP} reached)"
            continue
        recent = AnalysisSession.objects.filter(
            instrument=_instrument(symbol),
            user=user,
            created_at__gte=now - timedelta(minutes=DUPLICATE_WINDOW_MINUTES),
            market_context__analysis_mode="LIVE",
        ).exists()
        if recent:
            results[symbol] = (
                f"skipped (already run in the last {DUPLICATE_WINDOW_MINUTES} minutes)"
            )
            continue
        try:
            out = AnalysisService(user=user).analyze(
                symbol=symbol,
                timeframe="15m",
                session_type="MARKET_ANALYSIS",
                persist=True,
                forecast_horizon_minutes=SCHEDULED_HORIZON_MINUTES,
                paper_evaluate=True,
                analysis_mode="LIVE",
            )
            results[symbol] = f"saved session {out.get('session_id')}"
        except Exception as e:
            logger.error(
                f"Scheduled live analysis failed [{symbol}]: {type(e).__name__}"
            )
            results[symbol] = f"error: {type(e).__name__}"

    logger.info(f"Scheduled live analysis: {results}")
    return results


@shared_task
def write_daily_journal_draft():
    """17:00 IST on weekdays: write a draft journal entry summarising the day's runs."""
    from .services.journal_digest_service import JournalDigestService

    user = _pick_user() or _fallback_user()
    if user is None:
        return "skipped (no user)"
    return JournalDigestService.write_for_today(user)


def _fallback_user():
    """After the evening the Zerodha token may be unusable; use the last run's owner."""
    from .models import AnalysisSession

    last = (
        AnalysisSession.objects.exclude(user__isnull=True)
        .order_by("-created_at")
        .first()
    )
    return last.user if last else None
