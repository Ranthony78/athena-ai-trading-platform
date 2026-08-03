import time

from .base_ai_provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Mock AI provider for development and testing.
    Returns structured dummy responses without API calls.
    """

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict:
        """Return a mock AI analysis response."""

        start = time.time()

        content = """
## Market Analysis

**Session:** LIVE
**Bias:** NEUTRAL

### Market Structure
Price is trading near key support levels. No clear directional bias visible.

### Setup Assessment
**Signal:** NO_SETUP
**Confidence:** 45
**Reasoning:** Insufficient confluence of signals. Market is in consolidation phase.

### Key Levels
- **Resistance:** 24600
- **Support:** 24200
- **VWAP:** 24400

### Risk Factors
- High event risk this week
- Low volume confirmation
- VIX elevated

### Journal
```json
{
    "signal": "NO_SETUP",
    "confidence": 45,
    "confidence_level": "LOW",
    "target": null,
    "stop_loss": null,
    "key_levels": {
        "resistance": 24600,
        "support": 24200,
        "vwap": 24400
    },
    "risks": ["High event risk", "Low volume", "VIX elevated"]
}
```
"""

        duration_ms = int((time.time() - start) * 1000)

        return {
            "content": content.strip(),
            "model": model,
            "tokens_used": 450,
            "duration_ms": duration_ms,
        }