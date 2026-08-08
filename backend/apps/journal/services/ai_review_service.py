import logging
from django.utils import timezone

from apps.ai_engine.providers.ai_provider_factory import AIProviderFactory

from ..models import JournalEntry
from ..repositories.journal_repository import JournalEntryRepository

logger = logging.getLogger(__name__)


class AIReviewService:
    """
    Generates AI reviews for journal entries.
    Provides objective feedback on trading behavior and psychology.
    """

    SYSTEM_PROMPT = """You are a trading coach and psychologist reviewing a trader's journal.

Your role:
- Provide objective, constructive feedback
- Identify patterns in behavior and mistakes
- Highlight what the trader did well
- Suggest specific improvements
- Be direct but encouraging
- Focus on process, not just outcomes

Keep your review concise and actionable — maximum 300 words.
"""

    def review_entry(self, entry: JournalEntry) -> str:
        """
        Generate an AI review for a journal entry.

        Returns the review text.
        """
        try:
            prompt = self._build_prompt(entry)
            provider = AIProviderFactory.get_provider()

            result = provider.complete(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                model="claude-sonnet-4-6",
                max_tokens=600,
                temperature=0.4,
            )

            review = result["content"]

            # Save review to entry
            entry.ai_review = review
            entry.ai_reviewed_at = timezone.now()
            entry.save()

            return review

        except Exception as e:
            logger.error(f"AIReviewService error: {e}")
            return "AI review unavailable."

    def _build_prompt(self, entry: JournalEntry) -> str:
        """Build the review prompt from journal entry data."""

        trade_notes = entry.trade_notes.all()
        mistakes = [
            t.mistake_type for t in trade_notes
            if t.mistake_type != "NONE"
        ]

        return f"""
## Journal Entry Review Request

**Date:** {entry.date}
**Session:** {entry.session}
**Market Bias:** {entry.market_bias or 'Not specified'}
**Mood:** {entry.mood or 'Not specified'}
**Rating:** {entry.rating}/10

---

## Market Notes
{entry.market_notes or 'None'}

---

## Trade Summary
- Trades Taken: {entry.trades_taken}
- Winners: {entry.winners}
- Losers: {entry.losers}
- Total PnL: ₹{entry.total_pnl}

---

## Mistakes Made
{', '.join(mistakes) if mistakes else 'None'}

---

## What Worked
{entry.what_worked or 'Not specified'}

## What Didn't Work
{entry.what_didnt_work or 'Not specified'}

## Lessons Learned
{entry.lessons_learned or 'Not specified'}

---

Please review this journal entry and provide:
1. What the trader did well today
2. Key areas for improvement
3. Pattern observations (if any mistakes were made)
4. One specific actionable suggestion for tomorrow
""".strip()