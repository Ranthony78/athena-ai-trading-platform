import logging
from typing import Optional

from django.db.models import QuerySet
from django.utils.text import slugify

from ..models import Article, BookNote, Prompt, Tag, TradingRule
from ..repositories.knowledge_repository import (
    ArticleRepository,
    BookNoteRepository,
    PromptRepository,
    TagRepository,
    TradingRuleRepository,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Business logic for knowledge base management.
    """

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    @staticmethod
    def get_tags() -> QuerySet[Tag]:
        return TagRepository.active()

    @staticmethod
    def create_tag(data: dict) -> Tag:
        if "slug" not in data:
            data["slug"] = slugify(data["name"])
        return TagRepository.create(**data)

    # ------------------------------------------------------------------
    # Articles
    # ------------------------------------------------------------------

    @staticmethod
    def get_articles(
        user,
        category: str = None,
        tag_slug: str = None,
        featured: bool = False,
        limit: int = 50,
    ) -> QuerySet[Article]:
        """Return articles with optional filters."""
        if featured:
            return ArticleRepository.get_featured(user)
        if category:
            return ArticleRepository.get_by_category(user, category)
        if tag_slug:
            tag = TagRepository.get_by_slug(tag_slug)
            if tag:
                return ArticleRepository.get_by_tag(user, tag)
        return ArticleRepository.get_by_user(user, limit)

    @staticmethod
    def get_article(slug: str) -> Optional[Article]:
        """Return article by slug and increment view count."""
        article = ArticleRepository.get_by_slug(slug)
        if article:
            ArticleRepository.increment_views(article)
        return article

    @staticmethod
    def get_article_by_id(
        user,
        article_id: int,
    ) -> Optional[Article]:
        """Return article by ID for a user."""
        return ArticleRepository.first(
            id=article_id,
            user=user,
            is_active=True,
        )

    @staticmethod
    def create_article(user, data: dict) -> Article:
        """Create a new article."""
        tags = data.pop("tags", [])

        if "slug" not in data or not data["slug"]:
            data["slug"] = KnowledgeService._unique_slug(data["title"])

        data["user"] = user
        article = ArticleRepository.create(**data)

        if tags:
            article.tags.set(tags)

        return article

    @staticmethod
    def update_article(article: Article, data: dict) -> Article:
        """Update an existing article."""
        tags = data.pop("tags", None)
        article = ArticleRepository.update(article, **data)
        if tags is not None:
            article.tags.set(tags)
        return article

    @staticmethod
    def delete_article(article: Article) -> None:
        ArticleRepository.soft_delete(article)

    @staticmethod
    def search(user, query: str) -> QuerySet[Article]:
        """Search articles by title, content, summary."""
        return ArticleRepository.search(user, query)

    @staticmethod
    def _unique_slug(title: str) -> str:
        """Generate a unique slug from title."""
        base_slug = slugify(title)[:280]
        slug = base_slug
        counter = 1
        while ArticleRepository.exists(slug=slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    # ------------------------------------------------------------------
    # Book Notes
    # ------------------------------------------------------------------

    @staticmethod
    def get_books(user) -> QuerySet[BookNote]:
        return BookNoteRepository.get_by_user(user)

    @staticmethod
    def create_book(user, data: dict) -> BookNote:
        data["user"] = user
        return BookNoteRepository.create(**data)

    @staticmethod
    def get_book(
        user,
        book_id: int,
    ) -> Optional[BookNote]:
        return BookNoteRepository.first(id=book_id, user=user)

    @staticmethod
    def update_book(book: BookNote, data: dict) -> BookNote:
        return BookNoteRepository.update(book, **data)

    # ------------------------------------------------------------------
    # Trading Rules
    # ------------------------------------------------------------------

    @staticmethod
    def get_rules(
        user,
        rule_type: str = None,
    ) -> QuerySet[TradingRule]:
        return TradingRuleRepository.get_by_user(user, rule_type)

    @staticmethod
    def get_critical_rules(user) -> QuerySet[TradingRule]:
        return TradingRuleRepository.get_critical(user)

    @staticmethod
    def create_rule(user, data: dict) -> TradingRule:
        data["user"] = user
        if "rule_number" not in data:
            data["rule_number"] = TradingRuleRepository.get_next_rule_number(user)
        return TradingRuleRepository.create(**data)

    @staticmethod
    def update_rule(rule: TradingRule, data: dict) -> TradingRule:
        return TradingRuleRepository.update(rule, **data)

    @staticmethod
    def delete_rule(rule: TradingRule) -> None:
        TradingRuleRepository.soft_delete(rule)

    @staticmethod
    def record_rule_broken(rule_id: int, user) -> Optional[TradingRule]:
        """Record that a rule was broken."""
        rule = TradingRuleRepository.first(id=rule_id, user=user)
        if rule:
            return TradingRuleRepository.record_broken(rule)
        return None

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    @staticmethod
    def get_prompts(
        user,
        prompt_type: str = None,
    ) -> QuerySet[Prompt]:
        return PromptRepository.get_by_user(user, prompt_type)

    @staticmethod
    def get_public_prompts() -> QuerySet[Prompt]:
        return PromptRepository.get_public()

    @staticmethod
    def create_prompt(user, data: dict) -> Prompt:
        data["user"] = user
        return PromptRepository.create(**data)

    @staticmethod
    def use_prompt(prompt_id: int, user) -> Optional[Prompt]:
        """Increment use count and return prompt."""
        prompt = PromptRepository.first(id=prompt_id, user=user)
        if not prompt:
            prompt = PromptRepository.first(id=prompt_id, is_public=True)
        if prompt:
            PromptRepository.increment_use(prompt)
        return prompt

    @staticmethod
    def update_prompt(prompt: Prompt, data: dict) -> Prompt:
        return PromptRepository.update(prompt, **data)

    @staticmethod
    def delete_prompt(prompt: Prompt) -> None:
        PromptRepository.soft_delete(prompt)