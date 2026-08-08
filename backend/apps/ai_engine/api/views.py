import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.analysis_service import AnalysisService
from .serializers import (
    AISignalSerializer,
    AnalysisRequestSerializer,
    AnalysisSessionSerializer,
    PromptTemplateSerializer,
)

logger = logging.getLogger(__name__)


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

        try:
            service = AnalysisService(user=request.user)
            result = service.analyze(
                symbol=serializer.validated_data["symbol"].upper(),
                timeframe=serializer.validated_data["timeframe"],
                session_type=serializer.validated_data["session_type"],
                persist=serializer.validated_data["persist"],
            )
            return ApiResponse.success(data=result)
        except Exception as e:
            logger.error(f"AnalysisRunAPIView error: {e}")
            return ApiResponse.error(message="Analysis failed.")


class AnalysisSessionListAPIView(APIView):
    """
    GET /api/ai/sessions/
    Return today's analysis sessions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = AnalysisService.get_today_sessions()
        serializer = AnalysisSessionSerializer(sessions, many=True)
        return ApiResponse.success(serializer.data)


class AnalysisSessionDetailAPIView(APIView):
    """
    GET /api/ai/sessions/<id>/
    Return a single analysis session with full AI response.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        session = AnalysisService.get_session(pk)

        if not session:
            return ApiResponse.error(message="Session not found.")

        serializer = AnalysisSessionSerializer(session)
        return ApiResponse.success(serializer.data)


class AISignalListAPIView(APIView):
    """
    GET /api/ai/signals/
    Return today's AI signals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        signals = AnalysisService.get_today_signals()
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