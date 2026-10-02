from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.strategy_service import StrategyService
from .serializers import (
    StrategySerializer,
    StrategySignalSerializer,
)


class StrategyListAPIView(APIView):
    """
    GET  /api/strategies/          — list all strategies
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        strategies = StrategyService.get_all()
        serializer = StrategySerializer(strategies, many=True)
        return ApiResponse.success(serializer.data)


class StrategyDetailAPIView(APIView):
    """
    GET    /api/strategies/<id>/   — get strategy
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")
        return ApiResponse.success(StrategySerializer(strategy).data)


class StrategyRunAPIView(APIView):
    """
    POST /api/strategies/run/
    Retired endpoint. Rule-based strategy execution is no longer part of
    Athena's AI-led analysis workflow.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return ApiResponse.error(
            message="Rule-based strategy execution is retired. Use Athena's AI Workspace for new analysis.",
            status_code=410,
        )


class StrategyRunAllAPIView(APIView):
    """
    POST /api/strategies/run-all/
    Retired endpoint. Rule-based strategy execution is no longer part of
    Athena's AI-led analysis workflow.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return ApiResponse.error(
            message="Rule-based strategy execution is retired. Use Athena's AI Workspace for new analysis.",
            status_code=410,
        )


class SignalListAPIView(APIView):
    """
    GET /api/strategies/signals/          — today's signals
    GET /api/strategies/signals/?active=1 — active signals only
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get("active") == "1"

        if active_only:
            signals = StrategyService.get_active_signals()
        else:
            signals = StrategyService.get_today_signals()

        serializer = StrategySignalSerializer(signals, many=True)
        return ApiResponse.success(serializer.data)


class SignalBySymbolAPIView(APIView):
    """
    GET /api/strategies/signals/<symbol>/
    Return recent signals for a symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        signals = StrategyService.get_signals_for_instrument(symbol.upper())
        serializer = StrategySignalSerializer(signals, many=True)
        return ApiResponse.success(serializer.data)
