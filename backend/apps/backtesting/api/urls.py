from django.urls import path

from .views import (
    BacktestRunDetailAPIView,
    BacktestRunListAPIView,
    BacktestTradeListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------
    path(
        "runs/",
        BacktestRunListAPIView.as_view(),
        name="backtest-runs",
    ),
    path(
        "runs/<int:pk>/",
        BacktestRunDetailAPIView.as_view(),
        name="backtest-run-detail",
    ),

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------
    path(
        "runs/<int:pk>/trades/",
        BacktestTradeListAPIView.as_view(),
        name="backtest-trades",
    ),
]