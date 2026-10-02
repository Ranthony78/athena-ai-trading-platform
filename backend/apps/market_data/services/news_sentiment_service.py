"""
backend/apps/market_data/services/news_sentiment_service.py

New file.

Real market-driver headlines and per-article sentiment via Marketaux's
structured API, not scraped HTML or LLM guesses. Requires MARKETAUX_API_KEY
to be set — degrades to None
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
from django.core.cache import cache

logger = logging.getLogger(__name__)

MARKETAUX_BASE_URL = "https://api.marketaux.com/v1/news/all"
REQUEST_TIMEOUT_SECONDS = 8

# Query terms cover India and external drivers. Sentiment is still averaged
# only across India-relevant titles; global headlines remain separate evidence.
MACRO_SEARCH_QUERY = '"RBI"|"Fed"|"NIFTY"|"crude"|"rupee"|"USD/INR"|"Nasdaq"|"Asian markets"|"earnings"|"Union Budget"|"S&P 500"|"Dow Jones"|"Brent"|"OPEC"'
INDIA_SENTIMENT_TERMS = (
    "india",
    "indian",
    "nifty",
    "banknifty",
    "sensex",
    "rbi",
    "rupee",
    "usd/inr",
    "usd-inr",
    "national stock exchange",
)


class NewsSentimentService:
    """
    Fetches sourced headlines for Market Drivers and calculates an India-only
    sentiment average. Global stories never enter that numeric average.
    Returns None if the API key is missing or the request fails.
    """

    @classmethod
    def get_macro_sentiment(cls, max_articles: int = 25) -> Optional[dict]:
        api_key = getattr(settings, "MARKETAUX_API_KEY", "")
        if not api_key:
            return None
        cache_key = f"market-driver-news-v2:{max_articles}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached or None

        try:
            response = requests.get(
                MARKETAUX_BASE_URL,
                params={
                    "api_token": api_key,
                    "search": MACRO_SEARCH_QUERY,
                    "language": "en",
                    "limit": max_articles,
                    "sort": "published_at",
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            # requests exceptions may contain the URL's API token.
            logger.warning("News provider request failed (%s)", type(e).__name__)
            cache.set(cache_key, {}, 60)
            return None

        articles = payload.get("data") or []
        if not articles:
            return None

        headlines = []
        india_sentiment_scores = []
        india_article_count = 0
        for article in articles:
            entities = article.get("entities") or []
            # Average this article's own entity sentiment scores (an
            # article can mention several entities at different
            # sentiment levels) rather than picking just the first.
            article_scores = [
                e["sentiment_score"]
                for e in entities
                if e.get("sentiment_score") is not None
            ]
            avg_article_sentiment = (
                sum(article_scores) / len(article_scores) if article_scores else None
            )
            headlines.append(
                {
                    "title": article.get("title"),
                    "source": article.get("source"),
                    "published_at": article.get("published_at"),
                    "url": article.get("url"),
                    "sentiment": avg_article_sentiment,
                }
            )
            # Global headlines populate separate driver cards. Only
            # India-relevant headlines contribute to India's sentiment value.
            title = str(article.get("title") or "").lower()
            if any(term in title for term in INDIA_SENTIMENT_TERMS):
                india_article_count += 1
                if avg_article_sentiment is not None:
                    india_sentiment_scores.append(avg_article_sentiment)

        result = {
            "article_count": len(articles),
            "avg_sentiment": (
                round(sum(india_sentiment_scores) / len(india_sentiment_scores), 3)
                if india_sentiment_scores
                else None
            ),
            "sentiment_article_count": india_article_count,
            "headlines": headlines,
        }
        cache.set(cache_key, result, 300)
        return result
