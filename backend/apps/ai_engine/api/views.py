import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..repositories.ai_repository import PromptTemplateRepository
from ..services.analysis_service import AnalysisService
from ..services.prompt_service import PromptService
from ..services.provider_credentials import (
    ProviderCredentialService,
    ProviderEncryptionUnavailable,
)
from ..services.rule_evidence_service import RuleEvidenceService
from ..services.setup_strictness import LABELS as STRICTNESS_LABELS
from ..services.setup_strictness import LEVELS as STRICTNESS_LEVELS
from ..services.setup_strictness import get_level as get_setup_strictness
from .serializers import (
    AIProviderCredentialSerializer,
    AISignalSerializer,
    AnalysisRequestSerializer,
    AnalysisSessionSerializer,
    PromptTemplateSerializer,
)

logger = logging.getLogger(__name__)


class AnalysisPreferenceAPIView(APIView):
    """GET/PUT /api/ai/preferences/ - the user's setup strictness."""

    permission_classes = [IsAuthenticated]

    @staticmethod
    def _payload(user):
        level = get_setup_strictness(user)
        return {
            "setup_strictness": level,
            "options": [
                {"value": value, "label": STRICTNESS_LABELS[value]}
                for value in STRICTNESS_LEVELS
            ],
        }

    def get(self, request):
        return ApiResponse.success(data=self._payload(request.user))

    def put(self, request):
        level = str(request.data.get("setup_strictness", "")).upper()
        if level not in STRICTNESS_LEVELS:
            return ApiResponse.error(
                message="Choose Strict, Balanced or Exploratory.",
                errors={"setup_strictness": ["Invalid choice."]},
            )
        from ..models import AnalysisPreference

        AnalysisPreference.objects.update_or_create(
            user=request.user, defaults={"setup_strictness": level}
        )
        return ApiResponse.success(
            data=self._payload(request.user),
            message=f"Setup strictness set to {STRICTNESS_LABELS[level]}.",
        )


class ProviderConnectionAPIView(APIView):
    """Manage each user's encrypted provider key and run an explicit test call."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return ApiResponse.success(
            data=ProviderCredentialService.describe(request.user)
        )

    def put(self, request):
        serializer = AIProviderCredentialSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Enter a valid provider and API key.", errors=serializer.errors
            )
        values = serializer.validated_data
        try:
            ProviderCredentialService.save(
                request.user, values["provider"], values["api_key"]
            )
            return ApiResponse.success(
                data=ProviderCredentialService.describe(request.user),
                message="Your AI provider credentials were saved securely.",
            )
        except ProviderEncryptionUnavailable as exc:
            return ApiResponse.error(message=str(exc), status_code=503)
        except Exception as exc:
            logger.warning(
                "AI provider credentials could not be saved (%s).", type(exc).__name__
            )
            return ApiResponse.error(
                message="Could not save AI provider credentials.", status_code=500
            )

    def delete(self, request):
        ProviderCredentialService.delete(request.user)
        return ApiResponse.success(
            data=ProviderCredentialService.describe(request.user),
            message="Your personal AI provider credentials were removed.",
        )

    def post(self, request):
        try:
            config = ProviderCredentialService.resolve(request.user)
        except Exception as exc:
            logger.warning(
                "AI provider credentials could not be resolved (%s).",
                type(exc).__name__,
            )
            return ApiResponse.error(
                message="Saved AI credentials could not be read. Save the key again.",
                status_code=409,
            )
        if not config["configured"]:
            return ApiResponse.error(
                message="No AI provider key is configured for this account. Add one here to connect.",
                status_code=400,
            )

        try:
            from ..providers.ai_provider_factory import AIProviderFactory

            provider = AIProviderFactory.get_provider(
                config["provider"], api_key=config["api_key"] or None
            )
            result = provider.complete(
                system_prompt="You are performing a connection check. Do not provide market advice.",
                user_prompt="Reply with exactly: ATHENA_CONNECTION_OK",
                model=config["model"],
                # Gemini may spend part of the output budget on internal
                # reasoning; 16 tokens can end with MAX_TOKENS before the
                # short connection-check text is emitted.
                max_tokens=256,
                temperature=0,
            )
            if not str(result.get("content", "")).strip():
                raise ValueError("Provider returned an empty response.")
            return ApiResponse.success(
                data={
                    **{key: value for key, value in config.items() if key != "api_key"},
                    "connected": True,
                    "tested_at": timezone.now().isoformat(),
                    "response_time_ms": result.get("duration_ms"),
                    "verified_model": result.get("model") or config["model"],
                },
                message="AI provider connection test succeeded.",
            )
        except Exception as exc:
            # Provider exception messages can contain request details. Keep them
            # out of API responses and logs; the provider and exception type are enough to diagnose.
            logger.warning(
                "AI connection test failed for %s (%s).",
                config["provider"],
                type(exc).__name__,
            )
            return ApiResponse.error(
                message=f"Could not reach {config['provider_name']}. Check backend network access, provider credentials, model access, and quota.",
                errors={
                    "provider": config["provider"],
                    "error_type": type(exc).__name__,
                },
                status_code=502,
            )


class AnalysisPromptPreviewAPIView(APIView):
    """Build and return the exact analysis prompt without calling an AI provider."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid preview request.", errors=serializer.errors
            )

        values = serializer.validated_data
        symbol = values["symbol"].upper()
        timeframe = values["timeframe"]
        horizon = values["forecast_horizon_minutes"]
        session_type = values["session_type"]
        try:
            user_prompt, context = PromptService.build_market_analysis_prompt(
                symbol=symbol,
                timeframe=timeframe,
                user=request.user,
                forecast_horizon_minutes=horizon,
                analysis_mode=values["analysis_mode"],
            )
            template = PromptTemplateRepository.get_by_type(session_type)
            provider_config = ProviderCredentialService.describe(request.user)
            config = PromptService.request_config(
                template,
                provider=provider_config["provider"],
                model_override=provider_config["model"],
                setup_strictness=get_setup_strictness(request.user),
            )
            return ApiResponse.success(
                data={
                    "read_only": True,
                    "provider_call_made": False,
                    "actual_request": False,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "forecast_horizon_minutes": horizon,
                    "analysis_mode": values["analysis_mode"],
                    "provider": provider_config["provider"],
                    "model": config["model"],
                    "prompt_version": config["prompt_version"],
                    "template_source": config["template_source"],
                    "template_name": config["template_name"],
                    "generated_at": (context.get("rule_evidence") or {}).get("as_of"),
                    "system_prompt": config["system_prompt"],
                    "market_drivers": context.get("market_drivers"),
                    "prior_outcomes": context.get("prior_outcomes"),
                    "user_prompt": user_prompt,
                    "rule_evidence": context.get("rule_evidence"),
                    "parameters": (context.get("rule_evidence") or {}).get("parameters")
                    or RuleEvidenceService.parameters(),
                    "market_context_error": context.get("error"),
                }
            )
        except Exception as exc:
            logger.error(
                "Analysis prompt preview failed [%s] (%s)", symbol, type(exc).__name__
            )
            return ApiResponse.error(message="Could not build the analysis preview.")


class AnalysisRunAPIView(APIView):
    """
    POST /api/ai/analyze/
    Run a full AI market analysis for a symbol.

    Request body:
        {
            "symbol": "NIFTY",
            "timeframe": "15m",
            "session_type": "MARKET_ANALYSIS",
            "persist": true
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AnalysisRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        if not ProviderCredentialService.describe(request.user)["configured"]:
            return ApiResponse.error(
                message="Connect an AI provider and save your API key in Settings → AI Connection before requesting analysis.",
                status_code=400,
            )

        try:
            service = AnalysisService(user=request.user)
            result = service.analyze(
                symbol=serializer.validated_data["symbol"].upper(),
                timeframe=serializer.validated_data["timeframe"],
                session_type=serializer.validated_data["session_type"],
                persist=serializer.validated_data["persist"],
                forecast_horizon_minutes=serializer.validated_data[
                    "forecast_horizon_minutes"
                ],
                paper_evaluate=serializer.validated_data["paper_evaluate"],
                analysis_mode=serializer.validated_data["analysis_mode"],
            )
            return ApiResponse.success(data=result)
        except Exception as e:
            logger.error("AnalysisRunAPIView failed (%s).", type(e).__name__)
            return ApiResponse.error(message="Analysis failed.")


class AnalysisSessionListAPIView(APIView):
    """
    GET /api/ai/sessions/
    Return today's analysis sessions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ..models import AnalysisSession

        sessions = (
            AnalysisSession.objects.filter(user=request.user)
            .select_related("instrument", "template")
            .order_by("-session_time")[:200]
        )
        serializer = AnalysisSessionSerializer(sessions, many=True)
        return ApiResponse.success(serializer.data)

    def delete(self, request):
        """Permanently clear only the signed-in user's saved analysis sessions."""
        from ..models import AnalysisSession

        queryset = AnalysisSession.objects.filter(user=request.user)
        session_count = queryset.count()
        try:
            with transaction.atomic():
                deleted_records, _ = queryset.delete()
            return ApiResponse.success(
                data={
                    "sessions_deleted": session_count,
                    "records_deleted": deleted_records,
                }
            )
        except Exception as exc:
            logger.error("Analysis history clear failed (%s).", type(exc).__name__)
            return ApiResponse.error(message="Could not clear analysis history.")


class AnalysisSessionDetailAPIView(APIView):
    """
    GET /api/ai/sessions/<id>/
    Return a single analysis session with full AI response.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        session = AnalysisService.get_session(pk, user=request.user)

        if not session:
            return ApiResponse.error(message="Session not found.")

        serializer = AnalysisSessionSerializer(session)
        data = serializer.data
        data.update(
            system_prompt=session.system_prompt_used,
            user_prompt=session.prompt_used,
            market_context=session.market_context,
            actual_request=True,
        )
        if session.instrument_id:
            from ..services.confidence_calibration_service import (
                ConfidenceCalibrationService,
            )

            data["forecast_calibration"] = (
                ConfidenceCalibrationService.get_probability_report(
                    user=request.user,
                    symbol=session.instrument.symbol,
                    horizon_minutes=session.forecast_horizon_minutes,
                )
            )
            data["paper_trade_learning"] = (
                ConfidenceCalibrationService.get_paper_trade_report(
                    user=request.user,
                    symbol=session.instrument.symbol,
                )
            )
        return ApiResponse.success(data)


class AISignalListAPIView(APIView):
    """
    GET /api/ai/signals/
    Return today's AI signals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        signals = AnalysisService.get_today_signals(user=request.user)
        serializer = AISignalSerializer(signals, many=True)
        return ApiResponse.success(serializer.data)


class PromptTemplateListAPIView(APIView):
    """
    GET /api/ai/templates/
    Return all prompt templates.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ..repositories.ai_repository import PromptTemplateRepository

        templates = PromptTemplateRepository.active()
        serializer = PromptTemplateSerializer(templates, many=True)
        return ApiResponse.success(serializer.data)


class LearningReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ..services.learning_service import LearningService

        try:
            horizon = int(request.query_params.get("horizon", 15))
        except (ValueError, TypeError):
            return ApiResponse.error(message="Invalid horizon.")
        if horizon not in (5, 15, 30, 60):
            return ApiResponse.error(message="Unsupported forecast horizon.")
        return ApiResponse.success(
            LearningService.report(
                request.user,
                symbol=request.query_params.get("symbol", "NIFTY").upper(),
                horizon=horizon,
            )
        )


class MarketDriversAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ..services.market_drivers_service import MarketDriversService

        return ApiResponse.success(
            MarketDriversService.build(
                PromptService._safe_get_news_sentiment(),
                user=request.user,
            )
        )
