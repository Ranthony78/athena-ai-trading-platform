from django.urls import path

from .views import (  # Instruments; Sprint 11 — Market Engine; Sprint 12 — Indicators; Step 6 — Outcome Tracking Stats; Step 8 — Analysis Report
    AnalysisReportAPIView,
    BulkQuoteAPIView,
    ExpiryListAPIView,
    FuturesActivityAPIView,
    HistoricalDataAPIView,
    IndexListAPIView,
    IndicatorAPIView,
    IndicatorListAPIView,
    InstrumentDetailAPIView,
    InstrumentListAPIView,
    InstrumentSearchAPIView,
    MarketEngineStatusAPIView,
    MarketReadAPIView,
    MarketSessionAPIView,
    OptionChainAPIView,
    OptionChainSummaryAPIView,
    OptionsEngineAPIView,
    OutcomeStatsByStrategyAPIView,
    OutcomeStatsBySymbolAPIView,
    OutcomeStatsSummaryAPIView,
    ProfitProbabilityAPIView,
    QuoteDetailAPIView,
    QuoteListAPIView,
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
    path(
        "futures/<str:symbol>/activity/",
        FuturesActivityAPIView.as_view(),
        name="futures-activity",
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
    path(
        "option-chain/<str:symbol>/summary/",
        OptionChainSummaryAPIView.as_view(),
        name="option-chain-summary",
    ),
    path(
        "read/<str:symbol>/",
        MarketReadAPIView.as_view(),
        name="market-read",
    ),
    # ------------------------------------------------------------------
    # Analysis Report
    # ------------------------------------------------------------------
    path(
        "report/<str:symbol>/",
        AnalysisReportAPIView.as_view(),
        name="analysis-report",
    ),
    path(
        "options-engine/<str:symbol>/",
        OptionsEngineAPIView.as_view(),
        name="options-engine",
    ),
    path(
        "profit-probability/<str:symbol>/",
        ProfitProbabilityAPIView.as_view(),
        name="profit-probability",
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
    # ------------------------------------------------------------------
    # Step 6 — Outcome Tracking Stats
    # ------------------------------------------------------------------
    path(
        "outcomes/summary/",
        OutcomeStatsSummaryAPIView.as_view(),
        name="outcome-stats-summary",
    ),
    path(
        "outcomes/by-strategy/",
        OutcomeStatsByStrategyAPIView.as_view(),
        name="outcome-stats-by-strategy",
    ),
    path(
        "outcomes/by-symbol/",
        OutcomeStatsBySymbolAPIView.as_view(),
        name="outcome-stats-by-symbol",
    ),
]
