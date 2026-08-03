from django.urls import path

from .views import (
    ZerodhaConfigAPIView,
    ZerodhaFundsAPIView,
    ZerodhaHoldingsAPIView,
    ZerodhaLoginURLAPIView,
    ZerodhaLogoutAPIView,
    ZerodhaOrderCancelAPIView,
    ZerodhaOrderListAPIView,
    ZerodhaPositionsAPIView,
    ZerodhaProfileAPIView,
    ZerodhaStatusAPIView,
    ZerodhaTokenExchangeAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    path(
        "status/",
        ZerodhaStatusAPIView.as_view(),
        name="zerodha-status",
    ),
    path(
        "config/",
        ZerodhaConfigAPIView.as_view(),
        name="zerodha-config",
    ),
    path(
        "login-url/",
        ZerodhaLoginURLAPIView.as_view(),
        name="zerodha-login-url",
    ),
    path(
        "token/",
        ZerodhaTokenExchangeAPIView.as_view(),
        name="zerodha-token",
    ),
    path(
        "logout/",
        ZerodhaLogoutAPIView.as_view(),
        name="zerodha-logout",
    ),

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------
    path(
        "profile/",
        ZerodhaProfileAPIView.as_view(),
        name="zerodha-profile",
    ),
    path(
        "funds/",
        ZerodhaFundsAPIView.as_view(),
        name="zerodha-funds",
    ),

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    path(
        "orders/",
        ZerodhaOrderListAPIView.as_view(),
        name="zerodha-orders",
    ),
    path(
        "orders/<str:order_id>/cancel/",
        ZerodhaOrderCancelAPIView.as_view(),
        name="zerodha-order-cancel",
    ),

    # ------------------------------------------------------------------
    # Positions & Holdings
    # ------------------------------------------------------------------
    path(
        "positions/",
        ZerodhaPositionsAPIView.as_view(),
        name="zerodha-positions",
    ),
    path(
        "holdings/",
        ZerodhaHoldingsAPIView.as_view(),
        name="zerodha-holdings",
    ),
]