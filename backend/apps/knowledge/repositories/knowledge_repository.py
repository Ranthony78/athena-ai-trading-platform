from django.db import models
from typing import Optional
from django.db.models import QuerySet, F
from shared.repositories import BaseRepository
from ..models import Article, BookNote, Prompt, Tag, TradingRule


class TagRepository(BaseRepository[Tag]):

    model = Tag

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional[Tag]:
        return cls.model.objects.filter(slug=slug).first()

    @classmethod
    def get_by_name(cls, name: str) -> Optional[Tag]:
        return cls.model.objects.filter(name__iexact=name).first()


class ArticleRepository(BaseRepository[Article]):

    model = Article

    @classmethod
    def get_by_user(
        cls,
        user,
        limit: int = 50,
    ) -> QuerySet[Article]:
        """Return articles for a user."""
        return cls.model.objects.filter(
            user=user,
            is_active=True,
        ).prefetch_related("tags").order_by("-created_at")[:limit]

    @classmethod
    def get_by_category(
        cls,
        user,
        category: str,
    ) -> QuerySet[Article]:
        """Return articles by category."""
        return cls.model.objects.filter(
            user=user,
            category=category,
            is_active=True,
        ).prefetch_related("tags")

    @classmethod
    def get_by_tag(
        cls,
        user,
        tag: Tag,
    ) -> QuerySet[Article]:
        """Return articles with a specific tag."""
        return cls.model.objects.filter(
            user=user,
            tags=tag,
            is_active=True,
        ).prefetch_related("tags")

    @classmethod
    def get_featured(cls, user) -> QuerySet[Article]:
        """Return featured articles."""
        return cls.model.objects.filter(
            user=user,
            is_featured=True,
            is_active=True,
        ).prefetch_related("tags")

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional[Article]:
        """Return article by slug."""
        return cls.model.objects.filter(
            slug=slug,
            is_active=True,
        ).prefetch_related("tags").first()

    @classmethod
    def search(
        cls,
        user,
        query: str,
    ) -> QuerySet[Article]:
        """Full text search across title and content."""
        return cls.model.objects.filter(
            user=user,
            is_active=True,
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(content__icontains=query) |
            models.Q(summary__icontains=query)
        ).prefetch_related("tags")

    @classmethod
    def increment_views(cls, article: Article) -> None:
        """Increment view count atomically."""
        cls.model.objects.filter(pk=article.pk).update(
            view_count=F("view_count") + 1
        )


class BookNoteRepository(BaseRepository[BookNote]):

    model = BookNote

    @classmethod
    def get_by_user(cls, user) -> QuerySet[BookNote]:
        return cls.model.objects.filter(
            user=user,
            is_active=True,
        ).order_by("-created_at")


class TradingRuleRepository(BaseRepository[TradingRule]):

    model = TradingRule

    @classmethod
    def get_by_user(
        cls,
        user,
        rule_type: str = None,
    ) -> QuerySet[TradingRule]:
        """Return trading rules for a user."""
        qs = cls.model.objects.filter(
            user=user,
            is_active=True,
        )
        if rule_type:
            qs = qs.filter(rule_type=rule_type)
        return qs.order_by("rule_number")

    @classmethod
    def get_critical(cls, user) -> QuerySet[TradingRule]:
        """Return critical rules."""
        return cls.model.objects.filter(
            user=user,
            priority="CRITICAL",
            is_active=True,
        ).order_by("rule_number")

    @classmethod
    def get_next_rule_number(cls, user) -> int:
        """Return next available rule number."""
        last = cls.model.objects.filter(
            user=user,
        ).order_by("-rule_number").first()
        return (last.rule_number + 1) if last else 1

    @classmethod
    def record_broken(cls, rule: TradingRule) -> TradingRule:
        """Record that a rule was broken."""
        from django.utils import timezone
        rule.times_broken += 1
        rule.last_broken_at = timezone.now()
        rule.save()
        return rule


class PromptRepository(BaseRepository[Prompt]):

    model = Prompt

    @classmethod
    def get_by_user(
        cls,
        user,
        prompt_type: str = None,
    ) -> QuerySet[Prompt]:
        """Return prompts for a user."""
        qs = cls.model.objects.filter(
            user=user,
            is_active=True,
        )
        if prompt_type:
            qs = qs.filter(prompt_type=prompt_type)
        return qs.order_by("-use_count", "-created_at")

    @classmethod
    def get_public(cls) -> QuerySet[Prompt]:
        """Return public prompts."""
        return cls.model.objects.filter(
            is_public=True,
            is_active=True,
        ).order_by("-use_count")

    @classmethod
    def increment_use(cls, prompt: Prompt) -> None:
        """Increment use count."""
        cls.model.objects.filter(pk=prompt.pk).update(
            use_count=F("use_count") + 1
        )