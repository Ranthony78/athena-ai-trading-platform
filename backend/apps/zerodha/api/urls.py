from django.urls import path

from .views import (
    LiveTradingArmAPIView,
    LiveTradingDisarmAPIView,
    LiveTradingMasterAPIView,
    LiveTradingStatusAPIView,
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
    # Live-order permission
    # ------------------------------------------------------------------
    path("live-trading/", LiveTradingStatusAPIView.as_view(), name="live-trading"),
    path("live-trading/arm/", LiveTradingArmAPIView.as_view(), name="live-trading-arm"),
    path(
        "live-trading/disarm/",
        LiveTradingDisarmAPIView.as_view(),
        name="live-trading-disarm",
    ),
    path(
        "live-trading/master/",
        LiveTradingMasterAPIView.as_view(),
        name="live-trading-master",
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
