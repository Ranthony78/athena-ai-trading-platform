import logging
import time

import httpx

from django.conf import settings

from .base_ai_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    """Raised when the Groq API returns an error response."""
    pass


class GroqProvider(BaseAIProvider):
    """
    Groq AI provider — free-tier testing alternative to Claude.

    Groq exposes an OpenAI-compatible chat completions endpoint, so the
    request/response shape here differs from ClaudeProvider even though
    both implement the same BaseAIProvider interface.

    NOTE: model names are provider-specific. If a Claude-style model
    name (e.g. "claude-sonnet-4-6") gets passed in — which happens
    because AnalysisService's default is hardcoded to a Claude model —
    this provider substitutes its own default instead of sending an
    invalid model name to Groq. Check Groq's current model list at
    console.groq.com before relying on DEFAULT_MODEL long-term; model
    availability changes over time.
    """

    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self) -> None:
        self.api_key = getattr(settings, "GROQ_API_KEY", "")

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not set in settings or environment."
            )

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict:
        """
        Send a completion request to Groq's chat completions API.
        """
        start = time.time()

        # Substitute Groq's own default if a Claude-style model name
        # was passed through unchanged from AnalysisService's default.
        effective_model = model
        if model.lower().startswith("claude") or model.lower().startswith("gpt"):
            effective_model = self.DEFAULT_MODEL

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": effective_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            duration_ms = int((time.time() - start) * 1000)

            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            return {
                "content": content,
                "model": data.get("model", effective_model),
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API HTTP error: {e.response.status_code} — {e.response.text}")

            message = f"Groq API request failed with status {e.response.status_code}."
            try:
                body = e.response.json()
                api_message = body.get("error", {}).get("message")
                if api_message:
                    message = api_message
            except Exception:
                if e.response.text:
                    message = e.response.text

            raise GroqAPIError(message) from e

        except httpx.TimeoutException as e:
            logger.error("Groq API timeout.")
            raise GroqAPIError(
                "The Groq API did not respond in time. Please try again."
            ) from e

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
