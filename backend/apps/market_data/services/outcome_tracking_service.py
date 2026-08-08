"""
Automated outcome tracking for AISignal/StrategySignal.

Design: win/loss is determined by the real INDEX price hitting the
AI's actual predicted target/stop level (what it claimed) — not a
Delta-approximated option-premium target, which would be a lossy
conversion of something the AI never reasoned about directly. Once
an outcome resolves, the REAL option premium at that moment is
separately fetched and recorded, so both "was the call right" and
"what would that have actually been worth" are honest, real numbers.

MIS signals force-resolve at 15:15-15:20 IST if neither level hit.
NRML signals track until target/stop hit or the contract's real
expiry passes.
"""
import logging
from datetime import time

logger = logging.getLogger(__name__)

SQUARE_OFF_START = time(15, 15)
SQUARE_OFF_END = time(15, 20)


class OutcomeTrackingService:

    @classmethod
    def track_all_open_signals(cls) -> dict:
        """Entry point called by the scheduled Celery task."""
        from apps.ai_engine.models import AISignal
        from apps.strategies.models import StrategySignal
        from ..engine.market_state import MarketState

        now = MarketState.now_ist()
        checked = 0
        resolved = 0

        for model in (AISignal, StrategySignal):
            queryset = model.objects.filter(
                outcome_status="OPEN",
                option_instrument__isnull=False,
                user__isnull=False,
            ).select_related("instrument", "option_instrument", "user")

            for signal in queryset:
                checked += 1
                try:
                    if cls._check_signal(signal, now):
                        resolved += 1
                except Exception as e:
                    logger.error(
                        f"OutcomeTrackingService error "
                        f"[{model.__name__} id={signal.id}]: {e}"
                    )

        return {"checked": checked, "resolved": resolved}

    @classmethod
    def _check_signal(cls, signal, now) -> bool:
        """Returns True if this signal's outcome was resolved just now."""
        from .market_service import MarketService

        market = MarketService(user=signal.user)

        # 1. Check the real index price against the AI's actual
        #    predicted target/stop.
        quote = market.quote(signal.instrument.symbol)
        index_ltp = quote.get("ltp") if quote else None
        if not index_ltp:
            return False

        outcome = cls._determine_outcome(signal, index_ltp, now)
        if not outcome:
            return False  # still open

        # 2. Fetch the real option premium at this same moment.
        premium = cls._fetch_option_premium(signal)
        if premium is None:
            logger.warning(
                f"OutcomeTrackingService: outcome={outcome} for signal "
                f"{signal.id} but couldn't fetch real premium — leaving "
                f"OPEN rather than recording an incomplete outcome."
            )
            return False

        entry = float(signal.entry_premium) if signal.entry_premium else None
        points = round(premium - entry, 2) if entry else None
        points_pct = round((points / entry) * 100, 2) if points and entry else None

        signal.outcome_status = outcome
        signal.outcome_price = premium
        signal.outcome_time = now
        signal.points_captured = points
        signal.points_captured_pct = points_pct
        signal.save()

        logger.info(
            f"OutcomeTrackingService: signal {signal.id} resolved "
            f"{outcome} — {points_pct}% ({points} pts)"
        )
        return True

    @staticmethod
    def _determine_outcome(signal, index_ltp: float, now) -> str | None:
        """Returns an outcome status string, or None if still open."""
        direction = signal.signal
        target = float(signal.target_price) if signal.target_price else None
        stop = float(signal.stop_loss) if signal.stop_loss else None

        if direction == "BUY":
            if target and index_ltp >= target:
                return "TARGET_HIT"
            if stop and index_ltp <= stop:
                return "STOP_HIT"
        elif direction == "SELL":
            if target and index_ltp <= target:
                return "TARGET_HIT"
            if stop and index_ltp >= stop:
                return "STOP_HIT"

        # Time-based end conditions
        if signal.product == "MIS":
            if SQUARE_OFF_START <= now.time() <= SQUARE_OFF_END:
                return "SQUARED_OFF"
        elif signal.product == "NRML":
            expiry = signal.option_instrument.expiry
            if expiry and expiry <= now.date():
                return "EXPIRED"

        return None

    @staticmethod
    def _fetch_option_premium(signal) -> float | None:
        """Fetch the real current premium for the attached option contract."""
        try:
            from apps.zerodha.services.mcp_service import ZerodhaKiteMCPService

            service = ZerodhaKiteMCPService(signal.user)
            exchange_symbol = (
                f"{signal.option_instrument.exchange}:"
                f"{signal.option_instrument.trading_symbol}"
            )
            raw = service.get_quote(exchange_symbol)
            return raw.get("last_price") if raw else None
        except Exception as e:
            logger.error(
                f"OutcomeTrackingService premium fetch error "
                f"[signal {signal.id}]: {e}"
            )
            return None