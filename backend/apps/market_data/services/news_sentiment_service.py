"""
backend/apps/market_data/services/news_sentiment_service.py

New file.

Real news sentiment via Marketaux's structured API (real per-article
sentiment scores from actual financial press, not scraped HTML, not an
LLM guessing). Requires MARKETAUX_API_KEY to be set — degrades to None
(renders as NA everywhere downstream) if the key is missing or the
request fails for any reason.

Honest limitation, documented here rather than hidden: RBI is a central
bank, not a tradeable entity, so Marketaux can't target it via their
`symbols=` entity filter. This uses their free-text `search` parameter
instead, matched against India-country sources. That means the returned
sentiment_score is the *article's* sentiment toward whatever entity
happened to be co-mentioned (usually NIFTY/BANKNIFTY), not a dedicated
"RBI sentiment" score — a real but coarser signal than the VIX/breadth
numbers elsewhere in this pipeline. Treat this section's confidence
accordingly in the prompt.

Free tier: 100 requests/day, no card required (confirmed against
Marketaux's own docs as of Aug 2026). One call per analysis run comfortably
fits Athena's 3-5x/day volume — do not call this in a tight loop.
"""

import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MARKETAUX_BASE_URL = "https://api.marketaux.com/v1/news/all"
REQUEST_TIMEOUT_SECONDS = 8

# Keywords covering the macro events that actually move Nifty/Bank Nifty
# intraday. Kept short and specific — a broad match would pull in noise
# and burn through the free-tier daily quota faster for no real gain.
MACRO_SEARCH_QUERY = '"RBI"|"repo rate"|"inflation"|"Union Budget"|"Fed rate"'


class NewsSentimentService:
    """
    Fetches real, keyword-matched news sentiment for India-macro topics
    (RBI policy, rates, budget, Fed spillover) via Marketaux. Never
    fabricates — returns None if the API key isn't configured or the
    call fails, same pattern as every other service in this pipeline.
    """

    @classmethod
    def get_macro_sentiment(cls, max_articles: int = 5) -> Optional[dict]:
        api_key = getattr(settings, "MARKETAUX_API_KEY", "")
        if not api_key:
            return None

        try:
            response = requests.get(
                MARKETAUX_BASE_URL,
                params={
                    "api_token": api_key,
                    "search": MACRO_SEARCH_QUERY,
                    "countries": "in",
                    "language": "en",
                    "limit": max_articles,
                    "sort": "published_at",
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            logger.error(f"NewsSentimentService request failed: {e}")
            return None

        articles = payload.get("data") or []
        if not articles:
            return None

        headlines = []
        sentiment_scores = []
        for article in articles:
            entities = article.get("entities") or []
            # Average this article's own entity sentiment scores (an
            # article can mention several entities at different
            # sentiment levels) rather than picking just the first.
            article_scores = [
                e["sentiment_score"] for e in entities
                if e.get("sentiment_score") is not None
            ]
            avg_article_sentiment = (
                sum(article_scores) / len(article_scores)
                if article_scores else None
            )
            headlines.append({
                "title": article.get("title"),
                "source": article.get("source"),
                "published_at": article.get("published_at"),
                "sentiment": avg_article_sentiment,
            })
            if avg_article_sentiment is not None:
                sentiment_scores.append(avg_article_sentiment)

        return {
            "article_count": len(articles),
            "avg_sentiment": (
                round(sum(sentiment_scores) / len(sentiment_scores), 3)
                if sentiment_scores else None
            ),
            "headlines": headlines,
        }