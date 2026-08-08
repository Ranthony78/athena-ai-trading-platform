import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.strategy_service import StrategyService
from .serializers import (
    RunAllSerializer,
    RunStrategySerializer,
    StrategyCreateSerializer,
    StrategySerializer,
    StrategySignalSerializer,
)

logger = logging.getLogger(__name__)


class StrategyListAPIView(APIView):
    """
    GET  /api/strategies/          — list all strategies
    POST /api/strategies/          — create a strategy
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        strategies = StrategyService.get_all()
        serializer = StrategySerializer(strategies, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request):
        serializer = StrategyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        strategy = StrategyService.create(serializer.validated_data)
        return ApiResponse.success(
            data=StrategySerializer(strategy).data,
            message="Strategy created.",
        )


class StrategyDetailAPIView(APIView):
    """
    GET    /api/strategies/<id>/   — get strategy
    PUT    /api/strategies/<id>/   — update strategy
    DELETE /api/strategies/<id>/   — delete strategy
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")
        return ApiResponse.success(StrategySerializer(strategy).data)

    def put(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")

        serializer = StrategyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        updated = StrategyService.update(strategy, serializer.validated_data)
        return ApiResponse.success(
            data=StrategySerializer(updated).data,
            message="Strategy updated.",
        )

    def delete(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")
        StrategyService.delete(strategy)
        return ApiResponse.success(message="Strategy deleted.")


class StrategyRunAPIView(APIView):
    """
    POST /api/strategies/run/
    Run a single strategy against a symbol.

    Request body:
        { "strategy_id": 1, "symbol": "NIFTY" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunStrategySerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )
        try:
            result = StrategyService.run_strategy(
                strategy_id=serializer.validated_data["strategy_id"],
                symbol=serializer.validated_data["symbol"].upper(),
                user=request.user,
            )
            if not result:
                return ApiResponse.error(
                    message="Strategy returned no signal. Check candle data.",
                )
            return ApiResponse.success(data=result)
        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"StrategyRunAPIView error: {e}")
            return ApiResponse.error(message="Strategy execution failed.")


class StrategyRunAllAPIView(APIView):
    """
    POST /api/strategies/run-all/
    Run all enabled strategies against a list of symbols.

    Request body:
        { "symbols": ["NIFTY", "BANKNIFTY"] }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunAllSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )
        try:
            symbols = [s.upper() for s in serializer.validated_data["symbols"]]
            results = StrategyService.run_all(symbols, user=request.user)
            return ApiResponse.success(data=results)
        except Exception as e:
            logger.error(f"StrategyRunAllAPIView error: {e}")
            return ApiResponse.error(message="Strategy execution failed.")


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