import logging
import math
import hashlib
import json
from datetime import timedelta
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
from .output_validator import OutputValidator
from .prompt_service import PromptService
from .rule_evidence_service import RuleEvidenceService

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
        self.ai_service = AIService(user=user)
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
        forecast_horizon_minutes: int = 15,
        paper_evaluate: bool = False,
        analysis_mode: str = "LIVE",
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
                user=self.user,
                session_type=session_type,
                status="RUNNING",
                timeframe=timeframe,
                forecast_horizon_minutes=forecast_horizon_minutes,
            )

        user_prompt = None
        system_prompt = None
        market_context = {}
        template = None
        provider_call_made = False
        config = {}
        prompt_hash = None
        try:
            # Build prompt
            user_prompt, market_context = PromptService.build_market_analysis_prompt(
                symbol=symbol,
                timeframe=timeframe,
                user=self.user,
                forecast_horizon_minutes=forecast_horizon_minutes,
                analysis_mode=analysis_mode,
            )

            # Get system prompt
            template = PromptTemplateRepository.get_by_type(session_type)
            config = PromptService.request_config(
                template,
                provider=self.ai_service.provider_name,
                model_override=self.ai_service.provider_config["model"],
            )
            system_prompt = config["system_prompt"]
            model = config["model"]
            max_tokens = config["max_tokens"]
            prompt_hash = hashlib.sha256(json.dumps(
                [system_prompt, user_prompt], ensure_ascii=False,
            ).encode("utf-8")).hexdigest()
            if session:
                session.market_context = _sanitize_for_json(market_context)
                session.prompt_used = user_prompt
                session.system_prompt_used = system_prompt
                session.prompt_version = config["prompt_version"]
                session.prompt_hash = prompt_hash
                session.provider_used = self.ai_service.provider_name
                session.model_used = model
                session.template = template
                session.paper_evaluation = {"status": "REQUESTED" if paper_evaluate else "OFF"}
                session.save()

            # Call AI
            provider_call_made = True
            result = self.ai_service.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=config["temperature"],
            )

            parsed = result.get("parsed", {})

            validation = OutputValidator.validate(
                parsed=parsed,
                market_context=market_context,
                raw_content=result.get("content", ""),
            )
            parsed = validation["parsed"]
            for warning in validation["warnings"]:
                logger.warning(f"AnalysisService validation [{symbol}]: {warning}")

            # A separate, deterministic long-straddle gate. This is an
            # experimental paper candidate and never changes the AI signal.
            from .volatility_setup_service import VolatilitySetupService
            try:
                parsed["volatility_setup"] = VolatilitySetupService.build_candidate(
                    parsed=parsed, context=market_context, user=self.user,
                )
            except Exception as exc:
                logger.warning("Volatility setup evaluation unavailable (%s)", type(exc).__name__)
                parsed["volatility_setup"] = {
                    "version": VolatilitySetupService.VERSION,
                    "eligible": False, "status": "NOT_ELIGIBLE", "paper_only": True,
                    "experimental": True, "legs": [],
                    "reasons": ["The deterministic volatility gate could not verify all required evidence."],
                }

            signal_type = parsed.get("signal", "NO_SETUP")

            # Select a real tradable contract for directional signals,
            # regardless of whether this session gets persisted — the
            # frontend needs "what to buy" even for a quick, unsaved
            # analysis. Never fabricates a contract; None if unavailable.
            suggested_contract = None
            if signal_type in ("BUY", "SELL") and instrument:
                try:
                    from apps.market_data.services.strike_selection_service import (
                        StrikeSelectionService,
                    )
                    suggested_contract = StrikeSelectionService.select_for_signal(
                        symbol=instrument.symbol,
                        direction=signal_type,
                        user=self.user,
                        moneyness=parsed.get("option_moneyness", "ATM"),
                    )
                except Exception as e:
                    logger.error(f"AnalysisService strike selection error [{symbol}]: {e}")

            # Update session
            if persist and session:
                session.status = "COMPLETE"
                session.market_context = _sanitize_for_json(market_context)
                session.prompt_used = user_prompt
                session.ai_response = result["content"]
                session.parsed_output = parsed
                session.template = template
                session.model_used = result["model"]
                session.provider_used = result["provider"]
                session.tokens_used = result["tokens_used"]
                session.duration_ms = result["duration_ms"]
                session.probability_method_version = (
                    "horizon-base-rate-v1"
                    if market_context.get("intraday_probability_base_rate") else ""
                )
                session.forecast_sideways_band_pct = (
                    (market_context.get("intraday_probability_base_rate") or {}).get(
                        "sideways_band_pct", 0.05,
                    )
                )
                self._prepare_forecast(session, market_context)
                session.save()

                # Create AI signal if not neutral
                if signal_type in ("BUY", "SELL") and instrument:
                    self._create_signal(
                        session=session,
                        instrument=instrument,
                        parsed=parsed,
                        suggested_contract=suggested_contract,
                    )
                if paper_evaluate:
                    from .paper_evaluation_service import PaperEvaluationService
                    try:
                        PaperEvaluationService.start(session.id)
                    except Exception as exc:
                        logger.warning("Paper evaluation unavailable (%s)", type(exc).__name__)
                        session.paper_evaluation = {"status": "SKIPPED", "reason": "Paper evaluator unavailable; the analysis is still saved."}
                        session.save(update_fields=["paper_evaluation"])
                    session.refresh_from_db()

            return {
                "session_id": session.id if session else None,
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_mode": analysis_mode,
                "signal": parsed.get("signal", "NO_SETUP"),
                "confidence": parsed.get("confidence", 0),
                "confidence_level": parsed.get("confidence_level", "LOW"),
                "no_trade_reason": parsed.get("no_trade_reason"),
                "option_moneyness": parsed.get("option_moneyness"),
                "option_selection_reason": parsed.get("option_selection_reason"),
                "volatility_setup": parsed.get("volatility_setup"),
                "market_view": parsed.get("market_view"),
                "scenarios": parsed.get("scenarios"),
                "supporting_evidence": parsed.get("supporting_evidence"),
                "conflicting_evidence": parsed.get("conflicting_evidence"),
                "invalidation_conditions": parsed.get("invalidation_conditions"),
                "missing_information": parsed.get("missing_information"),
                "market_drivers": market_context.get("market_drivers"),
                "prior_outcomes": market_context.get("prior_outcomes"),
                "paper_evaluation": session.paper_evaluation if session else {"status": "OFF"},
                "target": parsed.get("target"),
                "stop_loss": parsed.get("stop_loss"),
                "key_levels": parsed.get("key_levels", {}),
                "risks": parsed.get("risks", []),
                "probability": parsed.get("probability"),
                "sentiment": parsed.get("sentiment"),
                "option_comparison": parsed.get("option_comparison"),
                "price_expectation": parsed.get("price_expectation"),
                "session_structure": market_context.get("session_structure"),
                "rule_evidence": _sanitize_for_json(market_context.get("rule_evidence")),
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "provider_call_made": provider_call_made,
                "validation_warnings": validation["warnings"],
                "suggested_contract": suggested_contract,
                "reasoning": result["content"],
                "tokens_used": result["tokens_used"],
                "duration_ms": result["duration_ms"],
                "model": result["model"],
                "provider": result["provider"],
                "prompt_version": config["prompt_version"],
                "template_source": config.get("template_source"),
                "template_name": config.get("template_name"),
                "prompt_hash": prompt_hash,
                "generated_at": (market_context.get("rule_evidence") or {}).get("as_of"),
                "forecast_tracking": self._forecast_tracking_payload(session),
                "forecast_calibration": self._get_probability_calibration(
                    symbol, forecast_horizon_minutes,
                ),
                "paper_trade_learning": self._get_paper_trade_report(symbol),
            }

        except Exception as e:
            logger.error(f"AnalysisService error [{symbol}]: {e}")

            if persist and session:
                session.status = "FAILED"
                session.error_message = str(e)
                session.provider_used = self.ai_service.provider_name
                if session.paper_evaluation.get("status") == "REQUESTED":
                    session.paper_evaluation = {"status": "SKIPPED", "reason": "Analysis failed; no paper entry."}
                session.save()

            return {
                "session_id": session.id if session else None,
                "symbol": symbol,
                "signal": "NO_SETUP",
                "error": str(e),
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "provider_call_made": provider_call_made,
                "rule_evidence": _sanitize_for_json(market_context.get("rule_evidence")),
                "market_drivers": market_context.get("market_drivers"),
                "prior_outcomes": market_context.get("prior_outcomes"),
                "parameters": (market_context.get("rule_evidence") or {}).get("parameters")
                or RuleEvidenceService.parameters(),
                "provider": self.ai_service.provider_name,
                "model": config.get("model"),
                "template_source": config.get("template_source"),
                "template_name": config.get("template_name"),
                "prompt_version": config.get("prompt_version"),
                "prompt_hash": prompt_hash,
                "generated_at": (market_context.get("rule_evidence") or {}).get("as_of"),
                "timeframe": timeframe,
                "analysis_mode": analysis_mode,
                "forecast_horizon_minutes": forecast_horizon_minutes,
            }

    # ------------------------------------------------------------------
    # Signal persistence
    # ------------------------------------------------------------------

    def _create_signal(
        self,
        session: AnalysisSession,
        instrument,
        parsed: dict,
        suggested_contract: dict = None,
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

        if suggested_contract:
            from apps.market_data.models import Instrument
            signal_kwargs["option_instrument"] = Instrument.objects.filter(
                id=suggested_contract["instrument_id"]
            ).first()
            signal_kwargs["entry_premium"] = suggested_contract["entry_premium"]

        return AISignal.objects.create(**signal_kwargs)

    @staticmethod
    def _forecast_tracking_payload(session):
        if not session:
            return None
        return {
            "status": session.forecast_outcome_status,
            "horizon_minutes": session.forecast_horizon_minutes,
            "target_time": session.forecast_target_time.isoformat()
            if session.forecast_target_time else None,
            "anchor_price": float(session.forecast_anchor_price)
            if session.forecast_anchor_price is not None else None,
            "actual_class": session.forecast_actual_class or None,
            "outcome_price": float(session.forecast_outcome_price)
            if session.forecast_outcome_price is not None else None,
            "resolved_at": session.forecast_resolved_at.isoformat()
            if session.forecast_resolved_at else None,
            "brier_score": float(session.forecast_brier_score)
            if session.forecast_brier_score is not None else None,
            "method_version": session.probability_method_version or None,
        }

    def _get_probability_calibration(self, symbol, horizon_minutes):
        try:
            from .confidence_calibration_service import ConfidenceCalibrationService

            return ConfidenceCalibrationService.get_probability_report(
                user=self.user,
                symbol=symbol,
                horizon_minutes=horizon_minutes,
            )
        except Exception as e:
            logger.warning(f"Probability calibration report unavailable [{symbol}]: {e}")
            return {"sample_size": 0, "note": "Calibration summary unavailable."}

    def _get_paper_trade_report(self, symbol):
        try:
            from .confidence_calibration_service import ConfidenceCalibrationService

            return ConfidenceCalibrationService.get_paper_trade_report(
                user=self.user,
                symbol=symbol,
            )
        except Exception as e:
            logger.warning(f"Paper trade report unavailable [{symbol}]: {e}")
            return {"sample_size": 0, "note": "Paper trade report unavailable."}

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    @staticmethod
    def get_today_sessions(user=None):
        """Return today's analysis sessions for one user."""
        return AnalysisSessionRepository.get_today(user=user)

    @staticmethod
    def get_today_signals(user=None):
        """Return today's AI signals for one user."""
        return AISignalRepository.get_today(user=user)

    @staticmethod
    def get_session(session_id: int, user=None):
        """Return a single session by ID for its owner."""
        if user is not None:
            return AnalysisSessionRepository.get_by_id_for_user(session_id, user)
        return AnalysisSessionRepository.get_by_id(session_id)
    @staticmethod
    def _prepare_forecast(session, context):
        """Track No Trade too; a numerical probability is optional for outcomes."""
        if context.get("analysis_mode") == "NEXT_SESSION":
            # This probability is anchored at the next session's open, not now;
            # the live-session outcome tracker cannot resolve that horizon.
            session.forecast_outcome_status = "NOT_TRACKED"
            return
        quote = context.get("quote") or {}
        try:
            anchor = float(quote.get("ltp"))
            stamp = datetime.fromisoformat(str(quote.get("timestamp")).replace("Z", "+00:00"))
            if timezone.is_naive(stamp):
                stamp = timezone.make_aware(stamp)
            local = timezone.localtime(stamp)
            target = stamp + timedelta(minutes=session.forecast_horizon_minutes)
            close = local.replace(hour=15, minute=30, second=0, microsecond=0)
            if (context.get("session") or {}).get("is_live") and context.get("quote_source") == "ZERODHA" and math.isfinite(anchor) and anchor > 0 and timedelta(0) <= timezone.now()-stamp <= timedelta(minutes=2) and timezone.now() < target <= close:
                session.forecast_anchor_price = anchor
                session.forecast_target_time = target
                session.forecast_outcome_status = "PENDING"
        except (ValueError, TypeError):
            pass
