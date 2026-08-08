import logging
import time

import httpx

from django.conf import settings

from .base_ai_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Raised when the Claude API returns an error response.
    Carries the actual message from Anthropic, not just the generic
    HTTP status text, so callers (and end users) see what really went
    wrong — e.g. 'Your credit balance is too low...' instead of a bare
    '400 Bad Request'.
    """
    pass


class ClaudeProvider(BaseAIProvider):
    """
    Anthropic Claude AI provider.
    Uses the Claude API for market analysis.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self) -> None:
        self.api_key = getattr(settings, "ANTHROPIC_API_KEY", "")

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set in settings or environment."
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
        Send a completion request to Claude API.
        """
        start = time.time()

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
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

            content = data["content"][0]["text"]
            tokens_used = data.get("usage", {}).get("input_tokens", 0) + \
                          data.get("usage", {}).get("output_tokens", 0)

            return {
                "content": content,
                "model": data.get("model", model),
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Claude API HTTP error: {e.response.status_code} — {e.response.text}")

            # Extract Anthropic's actual error message from the response
            # body so it can propagate to the caller (and eventually the
            # UI) instead of the generic httpx status text.
            message = f"Claude API request failed with status {e.response.status_code}."
            try:
                body = e.response.json()
                api_message = body.get("error", {}).get("message")
                if api_message:
                    message = api_message
            except Exception:
                # Response wasn't JSON — fall back to raw text if present
                if e.response.text:
                    message = e.response.text

            raise ClaudeAPIError(message) from e

        except httpx.TimeoutException as e:
            logger.error("Claude API timeout.")
            raise ClaudeAPIError(
                "The Claude API did not respond in time. Please try again."
            ) from e

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
