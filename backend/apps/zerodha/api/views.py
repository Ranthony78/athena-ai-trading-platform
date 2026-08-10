"""
backend/apps/zerodha/api/views.py

Replaces the existing file at this path.

Change from the previous version: views that call KiteService now catch
ZerodhaTokenExpiredError specifically and return HTTP 401 with a clear
message, instead of the generic except-Exception block returning a soft
error inside a 200 response. Every other view is unchanged from the
existing file.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..exceptions import ZerodhaTokenExpiredError
from ..services.auth_service import ZerodhaAuthService
from ..services.kite_service import KiteService
from .serializers import (
    OrderPlaceSerializer,
    TokenExchangeSerializer,
    ZerodhaConfigSerializer,
    ZerodhaConfigUpdateSerializer,
    ZerodhaSessionSerializer,
)

logger = logging.getLogger(__name__)

TOKEN_EXPIRED_MESSAGE = (
    "Your Zerodha session has expired. Please reconnect via "
    "/api/zerodha/login-url/."
)


class ZerodhaStatusAPIView(APIView):
    """
    GET /api/zerodha/status/
    Return Zerodha connection status.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            status_data = service.get_status()
            return ApiResponse.success(status_data)
        except Exception as e:
            logger.error(f"ZerodhaStatusAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch status.")


class ZerodhaConfigAPIView(APIView):
    """
    GET /api/zerodha/config/   — get config
    PUT /api/zerodha/config/   — save API key/secret
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            serializer = ZerodhaConfigSerializer(service.config)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"ZerodhaConfigAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch config.")

    def put(self, request):
        serializer = ZerodhaConfigUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            service = ZerodhaAuthService(request.user)
            config = service.save_config(serializer.validated_data)
            return ApiResponse.success(
                data=ZerodhaConfigSerializer(config).data,
                message="Zerodha config saved.",
            )
        except Exception as e:
            logger.error(f"ZerodhaConfigAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to save config.")


class ZerodhaLoginURLAPIView(APIView):
    """
    GET /api/zerodha/login-url/
    Get the Kite Connect login URL.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            url = service.get_login_url()
            return ApiResponse.success(
                data={"login_url": url},
                message="Visit this URL to login to Zerodha.",
            )
        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"ZerodhaLoginURLAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate login URL.")


class ZerodhaTokenExchangeAPIView(APIView):
    """
    POST /api/zerodha/token/
    Exchange request token for access token.
    Called after Kite Connect login redirect.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TokenExchangeSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            service = ZerodhaAuthService(request.user)
            result = service.exchange_token(
                serializer.validated_data["request_token"]
            )
            return ApiResponse.success(
                data=result,
                message="Zerodha login successful.",
            )
        except Exception as e:
            logger.error(f"ZerodhaTokenExchangeAPIView error: {e}")
            return ApiResponse.error(
                message=f"Token exchange failed: {str(e)}"
            )


class ZerodhaLogoutAPIView(APIView):
    """
    POST /api/zerodha/logout/
    Logout from Zerodha and revoke access token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            result = service.logout()
            return ApiResponse.success(message=result["message"])
        except Exception as e:
            logger.error(f"ZerodhaLogoutAPIView error: {e}")
            return ApiResponse.error(message="Logout failed.")


class ZerodhaProfileAPIView(APIView):
    """
    GET /api/zerodha/profile/
    Fetch Zerodha user profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            profile = service.get_profile()
            return ApiResponse.success(profile)
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaProfileAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch profile.")


class ZerodhaFundsAPIView(APIView):
    """
    GET /api/zerodha/funds/
    Fetch available funds and margins.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            funds = service.get_funds()
            return ApiResponse.success(funds)
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaFundsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch funds.")


class ZerodhaOrderListAPIView(APIView):
    """
    GET  /api/zerodha/orders/  — list today's orders
    POST /api/zerodha/orders/  — place a live order
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            orders = service.get_orders()
            return ApiResponse.success(orders)
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaOrderListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch orders.")

    def post(self, request):
        serializer = OrderPlaceSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid order data.",
                errors=serializer.errors,
            )
        try:
            service = KiteService(request.user)
            result = service.place_order(serializer.validated_data)
            return ApiResponse.success(
                data=result,
                message="Order placed.",
            )
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaOrderListAPIView POST error: {e}")
            return ApiResponse.error(message=f"Order failed: {str(e)}")


class ZerodhaOrderCancelAPIView(APIView):
    """
    POST /api/zerodha/orders/<order_id>/cancel/
    Cancel a live order.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id: str):
        try:
            service = KiteService(request.user)
            result = service.cancel_order(order_id)
            return ApiResponse.success(
                data=result,
                message="Order cancelled.",
            )
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaOrderCancelAPIView error: {e}")
            return ApiResponse.error(message=f"Cancel failed: {str(e)}")


class ZerodhaPositionsAPIView(APIView):
    """
    GET /api/zerodha/positions/
    Fetch current live positions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            positions = service.get_positions()
            return ApiResponse.success(positions)
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaPositionsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch positions.")


class ZerodhaHoldingsAPIView(APIView):
    """
    GET /api/zerodha/holdings/
    Fetch long-term holdings.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            holdings = service.get_holdings()
            return ApiResponse.success(holdings)
        except ZerodhaTokenExpiredError:
            return ApiResponse.error(
                message=TOKEN_EXPIRED_MESSAGE,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"ZerodhaHoldingsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch holdings.")