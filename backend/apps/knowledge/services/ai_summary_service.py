import logging
from django.utils import timezone

from apps.ai_engine.providers.ai_provider_factory import AIProviderFactory

from ..models import Article
from ..repositories.knowledge_repository import ArticleRepository

logger = logging.getLogger(__name__)


class AISummaryService:
    """
    Generates AI summaries for knowledge base articles.
    """

    SYSTEM_PROMPT = """You are a trading knowledge assistant.
Your task is to summarize trading articles and extract key points.

Output format:
1. A 2-3 sentence summary
2. A list of 3-5 key takeaways as bullet points

Keep it concise and practical for a trader.
"""

    def summarize(self, article: Article) -> dict:
        """
        Generate AI summary and key points for an article.

        Returns:
            {"summary": str, "key_points": list}
        """
        try:
            prompt = self._build_prompt(article)
            provider = AIProviderFactory.get_provider()

            result = provider.complete(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                model="claude-sonnet-4-6",
                max_tokens=500,
                temperature=0.3,
            )

            content = result["content"]

            # Parse summary and key points
            summary, key_points = self._parse_response(content)

            # Save to article
            article.ai_summary = summary
            article.ai_summarized_at = timezone.now()
            if not article.summary:
                article.summary = summary
            if not article.key_points:
                article.key_points = key_points
            article.save()

            return {
                "summary": summary,
                "key_points": key_points,
            }

        except Exception as e:
            logger.error(f"AISummaryService error: {e}")
            return {
                "summary": "Summary unavailable.",
                "key_points": [],
            }

    def _build_prompt(self, article: Article) -> str:
        return f"""
## Article to Summarize

**Title:** {article.title}
**Category:** {article.category}

**Content:**
{article.content[:3000]}

Please provide:
1. A 2-3 sentence summary
2. 3-5 key takeaways as bullet points
""".strip()

    def _parse_response(self, content: str) -> tuple[str, list]:
        """Parse AI response into summary and key points."""
        lines = content.strip().split("\n")
        summary_lines = []
        key_points = []
        in_points = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("•") or line.startswith("-") or line.startswith("*"):
                in_points = True
                point = line.lstrip("•-* ").strip()
                if point:
                    key_points.append(point)
            elif not in_points:
                summary_lines.append(line)

        summary = " ".join(summary_lines[:3])
        return summary, key_points[:5]