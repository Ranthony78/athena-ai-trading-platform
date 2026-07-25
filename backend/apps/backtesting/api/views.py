import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.backtest_service import BacktestService
from .serializers import (
    BacktestCreateSerializer,
    BacktestRunDetailSerializer,
    BacktestRunSerializer,
    BacktestTradeSerializer,
)

logger = logging.getLogger(__name__)


class BacktestRunListAPIView(APIView):
    """
    GET  /api/backtest/runs/  — list runs
    POST /api/backtest/runs/  — create and execute run
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 20))
            runs = BacktestService.get_runs(request.user, limit)
            serializer = BacktestRunSerializer(runs, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"BacktestRunListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch backtest runs.")

    def post(self, request):
        serializer = BacktestCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            # Create run
            run = BacktestService.create_run(
                user=request.user,
                data=serializer.validated_data,
            )

            # Execute synchronously
            result = BacktestService.execute(run)

            return ApiResponse.success(
                data=result,
                message="Backtest complete.",
            )

        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"BacktestRunListAPIView POST error: {e}")
            return ApiResponse.error(message="Backtest failed.")


class BacktestRunDetailAPIView(APIView):
    """
    GET /api/backtest/runs/<id>/
    Return full backtest run with result.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        run = BacktestService.get_run(request.user, pk)

        if not run:
            return ApiResponse.error(message="Backtest run not found.")

        serializer = BacktestRunDetailSerializer(run)
        return ApiResponse.success(serializer.data)


class BacktestTradeListAPIView(APIView):
    """
    GET /api/backtest/runs/<id>/trades/
    Return all trades for a backtest run.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        run = BacktestService.get_run(request.user, pk)

        if not run:
            return ApiResponse.error(message="Backtest run not found.")

        try:
            trades = BacktestService.get_trades(run)
            serializer = BacktestTradeSerializer(trades, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"BacktestTradeListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch trades.")