from django.urls import path

from .views import (
    AISignalListAPIView,
    AnalysisPreferenceAPIView,
    AnalysisPromptPreviewAPIView,
    AnalysisRunAPIView,
    AnalysisSessionDetailAPIView,
    AnalysisSessionListAPIView,
    LearningReportAPIView,
    MarketDriversAPIView,
    PromptTemplateListAPIView,
    ProviderConnectionAPIView,
)

urlpatterns = [
    path(
        "provider/", ProviderConnectionAPIView.as_view(), name="ai-provider-connection"
    ),
    path(
        "preferences/",
        AnalysisPreferenceAPIView.as_view(),
        name="ai-preferences",
    ),
    path("learning/", LearningReportAPIView.as_view(), name="ai-learning"),
    path("market-drivers/", MarketDriversAPIView.as_view(), name="ai-market-drivers"),
    path(
        "preview/",
        AnalysisPromptPreviewAPIView.as_view(),
        name="ai-prompt-preview",
    ),
    path(
        "analyze/",
        AnalysisRunAPIView.as_view(),
        name="ai-analyze",
    ),
    path(
        "sessions/",
        AnalysisSessionListAPIView.as_view(),
        name="ai-sessions",
    ),
    path(
        "sessions/<int:pk>/",
        AnalysisSessionDetailAPIView.as_view(),
        name="ai-session-detail",
    ),
    path(
        "signals/",
        AISignalListAPIView.as_view(),
        name="ai-signals",
    ),
    path(
        "templates/",
        PromptTemplateListAPIView.as_view(),
        name="ai-templates",
    ),
]
