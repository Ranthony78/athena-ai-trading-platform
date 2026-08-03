from django.urls import path

from .views import (
    OrderCancelAPIView,
    OrderListAPIView,
    PortfolioAPIView,
    PortfolioResetAPIView,
    PositionListAPIView,
    TodayOrdersAPIView,
    TodayTradesAPIView,
    TradeHistoryAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Portfolio
    # ------------------------------------------------------------------
    path(
        "portfolio/",
        PortfolioAPIView.as_view(),
        name="paper-portfolio",
    ),
    path(
        "portfolio/reset/",
        PortfolioResetAPIView.as_view(),
        name="paper-portfolio-reset",
    ),

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    path(
        "orders/",
        OrderListAPIView.as_view(),
        name="paper-orders",
    ),
    path(
        "orders/today/",
        TodayOrdersAPIView.as_view(),
        name="paper-orders-today",
    ),
    path(
        "orders/<int:pk>/cancel/",
        OrderCancelAPIView.as_view(),
        name="paper-order-cancel",
    ),

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------
    path(
        "positions/",
        PositionListAPIView.as_view(),
        name="paper-positions",
    ),

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------
    path(
        "trades/",
        TradeHistoryAPIView.as_view(),
        name="paper-trades",
    ),
    path(
        "trades/today/",
        TodayTradesAPIView.as_view(),
        name="paper-trades-today",
    ),
]