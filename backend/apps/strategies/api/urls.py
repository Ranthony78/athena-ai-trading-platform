from django.urls import path

from .views import (
    SignalBySymbolAPIView,
    SignalListAPIView,
    StrategyDetailAPIView,
    StrategyListAPIView,
    StrategyRunAllAPIView,
    StrategyRunAPIView,
)

urlpatterns = [
    # ------------------------------------------------------------------
    # Strategies
    # ------------------------------------------------------------------
    path(
        "",
        StrategyListAPIView.as_view(),
        name="strategy-list",
    ),
    path(
        "<int:pk>/",
        StrategyDetailAPIView.as_view(),
        name="strategy-detail",
    ),
    path(
        "run/",
        StrategyRunAPIView.as_view(),
        name="strategy-run",
    ),
    path(
        "run-all/",
        StrategyRunAllAPIView.as_view(),
        name="strategy-run-all",
    ),

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    path(
        "signals/",
        SignalListAPIView.as_view(),
        name="signal-list",
    ),
    path(
        "signals/<str:symbol>/",
        SignalBySymbolAPIView.as_view(),
        name="signal-by-symbol",
    ),
]