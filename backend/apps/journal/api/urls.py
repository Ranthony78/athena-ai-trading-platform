from django.urls import path

from .views import (
    JournalAIReviewAPIView,
    JournalEntryDetailAPIView,
    JournalEntryListAPIView,
    JournalStatsAPIView,
    LessonListAPIView,
    LessonReinforceAPIView,
    MistakeListAPIView,
    RuleListAPIView,
    TradeNoteListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Journal Entries
    # ------------------------------------------------------------------
    path(
        "entries/",
        JournalEntryListAPIView.as_view(),
        name="journal-entries",
    ),
    path(
        "entries/<int:pk>/",
        JournalEntryDetailAPIView.as_view(),
        name="journal-entry-detail",
    ),
    path(
        "entries/<int:pk>/review/",
        JournalAIReviewAPIView.as_view(),
        name="journal-ai-review",
    ),
    path(
        "entries/<int:pk>/notes/",
        TradeNoteListAPIView.as_view(),
        name="journal-trade-notes",
    ),

    # ------------------------------------------------------------------
    # Stats & Analysis
    # ------------------------------------------------------------------
    path(
        "stats/",
        JournalStatsAPIView.as_view(),
        name="journal-stats",
    ),
    path(
        "mistakes/",
        MistakeListAPIView.as_view(),
        name="journal-mistakes",
    ),

    # ------------------------------------------------------------------
    # Lessons & Rules
    # ------------------------------------------------------------------
    path(
        "lessons/",
        LessonListAPIView.as_view(),
        name="journal-lessons",
    ),
    path(
        "lessons/<int:pk>/reinforce/",
        LessonReinforceAPIView.as_view(),
        name="journal-lesson-reinforce",
    ),
    path(
        "rules/",
        RuleListAPIView.as_view(),
        name="journal-rules",
    ),
]