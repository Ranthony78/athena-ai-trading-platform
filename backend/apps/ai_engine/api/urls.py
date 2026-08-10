from django.urls import path

from .views import (
    AISignalListAPIView,
    AnalysisRunAPIView,
    AnalysisSessionDetailAPIView,
    AnalysisSessionListAPIView,
    PromptTemplateListAPIView,
)

urlpatterns = [
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