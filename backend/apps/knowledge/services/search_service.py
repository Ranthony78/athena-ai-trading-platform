import logging

from django.db.models import Q

from ..repositories.knowledge_repository import (
    ArticleRepository,
    TradingRuleRepository,
    PromptRepository,
)

logger = logging.getLogger(__name__)


class SearchService:
    """
    Full text search across the knowledge base.
    """

    @staticmethod
    def search(user, query: str) -> dict:
        """
        Search all knowledge base content.
        """
        if not query or len(query) < 2:
            return {
                "articles": [],
                "rules": [],
                "prompts": [],
                "total": 0,
            }

        articles = ArticleRepository.filter(
            user=user,
            is_active=True,
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(summary__icontains=query)
        ).prefetch_related("tags")[:10]

        rules = TradingRuleRepository.filter(
            user=user,
            is_active=True,
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]

        prompts = PromptRepository.filter(
            user=user,
            is_active=True,
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )[:5]

        return {
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "slug": a.slug,
                    "category": a.category,
                    "summary": a.summary[:200] if a.summary else "",
                }
                for a in articles
            ],
            "rules": [
                {
                    "id": r.id,
                    "rule_number": r.rule_number,
                    "title": r.title,
                    "rule_type": r.rule_type,
                    "priority": r.priority,
                }
                for r in rules
            ],
            "prompts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "prompt_type": p.prompt_type,
                    "description": p.description[:200],
                }
                for p in prompts
            ],
            "total": articles.count() + rules.count() + prompts.count(),
        }