import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.order_service import OrderService
from ..services.portfolio_service import PortfolioService
from ..services.position_service import PositionService
from .serializers import (
    PaperOrderSerializer,
    PaperPositionSerializer,
    PaperTradeSerializer,
    PlaceOrderSerializer,
)

logger = logging.getLogger(__name__)


class PortfolioAPIView(APIView):
    """
    GET /api/paper/portfolio/
    Return full portfolio summary.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = PortfolioService.get_portfolio(request.user)
            return ApiResponse.success(data)
        except Exception as e:
            logger.error(f"PortfolioAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch portfolio.")


class PortfolioResetAPIView(APIView):
    """
    POST /api/paper/portfolio/reset/
    Reset paper trading account to initial state.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            result = PortfolioService.reset_account(request.user)
            return ApiResponse.success(data=result)
        except Exception as e:
            logger.error(f"PortfolioResetAPIView error: {e}")
            return ApiResponse.error(message="Failed to reset account.")


class OrderListAPIView(APIView):
    """
    GET  /api/paper/orders/        — list orders
    POST /api/paper/orders/        — place order
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            status = request.query_params.get("status")
            service = OrderService()
            orders = service.get_orders(request.user, status)
            serializer = PaperOrderSerializer(orders, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"OrderListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch orders.")

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            service = OrderService()
            result = service.place_order(
                user=request.user,
                symbol=serializer.validated_data["symbol"].upper(),
                transaction_type=serializer.validated_data["transaction_type"],
                quantity=serializer.validated_data["quantity"],
                order_type=serializer.validated_data["order_type"],
                price=serializer.validated_data["price"],
                product=serializer.validated_data["product"],
                tag=serializer.validated_data["tag"],
            )

            if result["success"]:
                return ApiResponse.success(
                    data=result,
                    message="Order placed successfully.",
                )
            return ApiResponse.error(message=result["message"])

        except Exception as e:
            logger.error(f"OrderListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to place order.")


class OrderCancelAPIView(APIView):
    """
    POST /api/paper/orders/<id>/cancel/
    Cancel a pending order.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            service = OrderService()
            result = service.cancel_order(request.user, pk)

            if result["success"]:
                return ApiResponse.success(data=result)
            return ApiResponse.error(message=result["message"])

        except Exception as e:
            logger.error(f"OrderCancelAPIView error: {e}")
            return ApiResponse.error(message="Failed to cancel order.")


class TodayOrdersAPIView(APIView):
    """
    GET /api/paper/orders/today/
    Return today's orders.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = OrderService()
            orders = service.get_today_orders(request.user)
            serializer = PaperOrderSerializer(orders, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TodayOrdersAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch today's orders.")


class PositionListAPIView(APIView):
    """
    GET /api/paper/positions/
    Return all open positions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            positions = PositionService.get_open_positions(request.user)
            serializer = PaperPositionSerializer(positions, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"PositionListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch positions.")


class TradeHistoryAPIView(APIView):
    """
    GET /api/paper/trades/
    Return completed trade history.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 50))
            trades = PortfolioService.get_trade_history(request.user, limit)
            serializer = PaperTradeSerializer(trades, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TradeHistoryAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch trade history.")


class TodayTradesAPIView(APIView):
    """
    GET /api/paper/trades/today/
    Return today's completed trades.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trades = PortfolioService.get_today_trades(request.user)
            serializer = PaperTradeSerializer(trades, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TodayTradesAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch today's trades.")