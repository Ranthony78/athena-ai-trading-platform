from django.urls import path

from .views import (
    ArticleDetailAPIView,
    ArticleListAPIView,
    ArticleSummarizeAPIView,
    BookNoteDetailAPIView,
    BookNoteListAPIView,
    KnowledgeSearchAPIView,
    PromptListAPIView,
    PromptUseAPIView,
    TagListAPIView,
    TradingRuleBrokenAPIView,
    TradingRuleDetailAPIView,
    TradingRuleListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    path(
        "search/",
        KnowledgeSearchAPIView.as_view(),
        name="knowledge-search",
    ),

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------
    path(
        "tags/",
        TagListAPIView.as_view(),
        name="knowledge-tags",
    ),

    # ------------------------------------------------------------------
    # Articles
    # ------------------------------------------------------------------
    path(
        "articles/",
        ArticleListAPIView.as_view(),
        name="knowledge-articles",
    ),
    path(
        "articles/<slug:slug>/",
        ArticleDetailAPIView.as_view(),
        name="knowledge-article-detail",
    ),
    path(
        "articles/<slug:slug>/summarize/",
        ArticleSummarizeAPIView.as_view(),
        name="knowledge-article-summarize",
    ),

    # ------------------------------------------------------------------
    # Books
    # ------------------------------------------------------------------
    path(
        "books/",
        BookNoteListAPIView.as_view(),
        name="knowledge-books",
    ),
    path(
        "books/<int:pk>/",
        BookNoteDetailAPIView.as_view(),
        name="knowledge-book-detail",
    ),

    # ------------------------------------------------------------------
    # Trading Rules
    # ------------------------------------------------------------------
    path(
        "rules/",
        TradingRuleListAPIView.as_view(),
        name="knowledge-rules",
    ),
    path(
        "rules/<int:pk>/",
        TradingRuleDetailAPIView.as_view(),
        name="knowledge-rule-detail",
    ),
    path(
        "rules/<int:pk>/broken/",
        TradingRuleBrokenAPIView.as_view(),
        name="knowledge-rule-broken",
    ),

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    path(
        "prompts/",
        PromptListAPIView.as_view(),
        name="knowledge-prompts",
    ),
    path(
        "prompts/<int:pk>/use/",
        PromptUseAPIView.as_view(),
        name="knowledge-prompt-use",
    ),
]