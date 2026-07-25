from django.urls import path

from .views import (
    # Instruments
    BulkQuoteAPIView,
    ExpiryListAPIView,
    HistoricalDataAPIView,
    IndexListAPIView,
    InstrumentDetailAPIView,
    InstrumentListAPIView,
    InstrumentSearchAPIView,
    OptionChainAPIView,
    QuoteDetailAPIView,
    QuoteListAPIView,
    # Sprint 11 — Market Engine
    MarketEngineStatusAPIView,
    MarketSessionAPIView,
    # Sprint 12 — Indicators
    IndicatorAPIView,
    IndicatorListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Instruments
    # ------------------------------------------------------------------
    path(
        "instruments/",
        InstrumentListAPIView.as_view(),
        name="instrument-list",
    ),
    path(
        "instruments/search/",
        InstrumentSearchAPIView.as_view(),
        name="instrument-search",
    ),
    path(
        "instruments/<str:symbol>/",
        InstrumentDetailAPIView.as_view(),
        name="instrument-detail",
    ),

    # ------------------------------------------------------------------
    # Indices
    # ------------------------------------------------------------------
    path(
        "indices/",
        IndexListAPIView.as_view(),
        name="index-list",
    ),

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------
    path(
        "quotes/",
        QuoteListAPIView.as_view(),
        name="quote-list",
    ),
    path(
        "quotes/bulk/",
        BulkQuoteAPIView.as_view(),
        name="quote-bulk",
    ),
    path(
        "quotes/<str:symbol>/",
        QuoteDetailAPIView.as_view(),
        name="quote-detail",
    ),

    # ------------------------------------------------------------------
    # Historical Data
    # ------------------------------------------------------------------
    path(
        "historical/<str:symbol>/",
        HistoricalDataAPIView.as_view(),
        name="historical-data",
    ),

    # ------------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------------
    path(
        "expiry/<str:symbol>/",
        ExpiryListAPIView.as_view(),
        name="expiry-list",
    ),

    # ------------------------------------------------------------------
    # Option Chain
    # ------------------------------------------------------------------
    path(
        "option-chain/<str:symbol>/",
        OptionChainAPIView.as_view(),
        name="option-chain",
    ),

    # ------------------------------------------------------------------
    # Sprint 11 — Market Engine
    # ------------------------------------------------------------------
    path(
        "session/",
        MarketSessionAPIView.as_view(),
        name="market-session",
    ),
    path(
        "engine/status/",
        MarketEngineStatusAPIView.as_view(),
        name="engine-status",
    ),

    # ------------------------------------------------------------------
    # Sprint 12 — Technical Indicators
    # ------------------------------------------------------------------
    path(
        "indicators/",
        IndicatorListAPIView.as_view(),
        name="indicator-list",
    ),
    path(
        "indicators/calculate/",
        IndicatorAPIView.as_view(),
        name="indicator-calculate",
    ),
]