import logging
import math
from datetime import datetime

from django.utils import timezone

from apps.market_data.repositories.instrument_repository import InstrumentRepository

from ..models import AISignal, AnalysisSession
from ..repositories.ai_repository import (
    AISignalRepository,
    AnalysisSessionRepository,
    PromptTemplateRepository,
)
from .ai_service import AIService
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


def _sanitize_for_json(value):
    """
    Recursively replace non-finite floats (NaN, Infinity, -Infinity)
    with None. Python's json.dumps() happily serializes these as
    literal tokens, but they aren't valid per the JSON spec — SQLite's
    strict JSON_VALID() check correctly rejects them, which is what
    was failing here. None is the honest choice: it means "this
    specific value couldn't be computed," matching the project's
    real-data-or-NA principle, rather than fabricating a placeholder
    number.
    """
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    return value


class AnalysisService:
    """
    Orchestrates the full AI analysis pipeline.
    Builds prompt → calls AI → parses response → persists session + signal.
    """

    def __init__(self, user=None) -> None:
        self.ai_service = AIService()
        self.user = user

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyze(
        self,
        symbol: str,
        timeframe: str = "15m",
        session_type: str = "MARKET_ANALYSIS",
        persist: bool = True,
    ) -> dict:
        """
        Run a full AI analysis for a symbol.

        Args:
            symbol:       Instrument symbol e.g. 'NIFTY'
            timeframe:    Candle timeframe e.g. '15m'
            session_type: Type of analysis
            persist:      Save session and signal to DB

        Returns:
            Full analysis result dict
        """
        instrument = InstrumentRepository.get_by_symbol(symbol)

        # Create session record
        session = None
        if persist:
            session = AnalysisSession.objects.create(
                instrument=instrument,
                session_type=session_type,
                status="RUNNING",
                timeframe=timeframe,
            )

        try:
            # Build prompt
            user_prompt, market_context = PromptService.build_market_analysis_prompt(
                symbol=symbol,
                timeframe=timeframe,
                user=self.user,
            )

            # Get system prompt
            template = PromptTemplateRepository.get_by_type(session_type)
            system_prompt = (
                template.system_prompt
                if template
                else PromptService.DEFAULT_SYSTEM_PROMPT
            )
            model = template.model if template else "claude-sonnet-4-6"
            max_tokens = template.max_tokens if template else 4000

            # Call AI
            result = self.ai_service.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
            )

            parsed = result.get("parsed", {})

            # Update session
            if persist and session:
                session.status = "COMPLETE"
                session.market_context = _sanitize_for_json(market_context)
                session.prompt_used = user_prompt
                session.ai_response = result["content"]
                session.parsed_output = parsed
                session.model_used = result["model"]
                session.tokens_used = result["tokens_used"]
                session.duration_ms = result["duration_ms"]
                session.save()

                # Create AI signal if not neutral
                signal_type = parsed.get("signal", "NO_SETUP")
                if signal_type not in ("NEUTRAL", "NO_SETUP") and instrument:
                    self._create_signal(
                        session=session,
                        instrument=instrument,
                        parsed=parsed,
                    )

            return {
                "session_id": session.id if session else None,
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": parsed.get("signal", "NO_SETUP"),
                "confidence": parsed.get("confidence", 0),
                "confidence_level": parsed.get("confidence_level", "LOW"),
                "target": parsed.get("target"),
                "stop_loss": parsed.get("stop_loss"),
                "key_levels": parsed.get("key_levels", {}),
                "risks": parsed.get("risks", []),
                "reasoning": result["content"],
                "tokens_used": result["tokens_used"],
                "duration_ms": result["duration_ms"],
                "model": result["model"],
            }

        except Exception as e:
            logger.error(f"AnalysisService error [{symbol}]: {e}")

            if persist and session:
                session.status = "FAILED"
                session.error_message = str(e)
                session.save()

            return {
                "session_id": session.id if session else None,
                "symbol": symbol,
                "signal": "NO_SETUP",
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # Signal persistence
    # ------------------------------------------------------------------

    def _create_signal(
        self,
        session: AnalysisSession,
        instrument,
        parsed: dict,
    ) -> AISignal:
        """Create and persist an AI signal from parsed output."""

        confidence_score = int(parsed.get("confidence", 0))
        confidence_level = parsed.get("confidence_level", "LOW")

        if confidence_score >= 70:
            confidence_level = "HIGH"
        elif confidence_score >= 45:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        signal_type = parsed.get("signal", "NO_SETUP")

        # Step 3: attach a real option contract for directional signals
        # (BUY/SELL). Returns None for WATCH, or if the option chain
        # isn't available (e.g. no user, or NFO data missing) — the
        # signal is still saved either way, just without a contract.
        option_data = None
        try:
            from apps.market_data.services.strike_selection_service import (
                StrikeSelectionService,
            )
            option_data = StrikeSelectionService.select_for_signal(
                symbol=instrument.symbol,
                direction=signal_type,
                user=self.user,
            )
        except Exception as e:
            logger.error(f"AnalysisService strike selection error: {e}")

        signal_kwargs = dict(
            session=session,
            instrument=instrument,
            user=self.user,
            signal=signal_type,
            confidence=confidence_level,
            confidence_score=confidence_score,
            price_at_signal=parsed.get("price"),
            target_price=parsed.get("target"),
            stop_loss=parsed.get("stop_loss"),
            reasoning=session.ai_response,
            key_levels=parsed.get("key_levels", {}),
            risks=parsed.get("risks", []),
            signal_time=timezone.now(),
        )

        if option_data:
            from apps.market_data.models import Instrument
            signal_kwargs["option_instrument"] = Instrument.objects.filter(
                id=option_data["instrument_id"]
            ).first()
            signal_kwargs["entry_premium"] = option_data["entry_premium"]

        return AISignal.objects.create(**signal_kwargs)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    @staticmethod
    def get_today_sessions():
        """Return all analysis sessions from today."""
        return AnalysisSessionRepository.get_today()

    @staticmethod
    def get_today_signals():
        """Return all AI signals from today."""
        return AISignalRepository.get_today()

    @staticmethod
    def get_session(session_id: int):
        """Return a single session by ID."""
        return AnalysisSessionRepository.get_by_id(session_id)