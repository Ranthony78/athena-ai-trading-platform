import logging
import random
import time

import httpx
from django.conf import settings

from .base_ai_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Raised when Gemini cannot return a usable completion."""


class GeminiProvider(BaseAIProvider):
    """Google Gemini implementation of Athena's shared AI provider contract."""

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    DEFAULT_MODEL = "gemini-3.5-flash"
    REQUEST_TIMEOUT_SECONDS = 60.0
    MAX_UNAVAILABLE_RETRIES = 3

    def __init__(self, api_key=None) -> None:
        self.api_key = (
            api_key if api_key is not None else getattr(settings, "GEMINI_API_KEY", "")
        )
        self.default_model = getattr(settings, "GEMINI_MODEL", self.DEFAULT_MODEL)
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured on the backend.")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict:
        # Prompt templates may still carry a Claude model name. Never send a
        # model identifier from another provider to Gemini.
        effective_model = (
            model if model and model.startswith("gemini-") else self.default_model
        )
        if not effective_model:
            raise ValueError("GEMINI_MODEL is not configured on the backend.")

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        start = time.monotonic()

        data = None
        for attempt in range(self.MAX_UNAVAILABLE_RETRIES + 1):
            try:
                response = httpx.post(
                    self.API_URL.format(model=effective_model),
                    headers={"x-goog-api-key": self.api_key},
                    json=payload,
                    timeout=self.REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                data = response.json()
                break
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 503 and attempt < self.MAX_UNAVAILABLE_RETRIES:
                    base_delay = min(8.0, 0.8 * (2**attempt))
                    delay = random.uniform(base_delay, base_delay * 1.5)
                    logger.warning(
                        "Gemini returned HTTP 503; retry %s/%s after %.1fs.",
                        attempt + 1,
                        self.MAX_UNAVAILABLE_RETRIES,
                        delay,
                    )
                    time.sleep(delay)
                    continue

                logger.warning("Gemini API returned HTTP %s.", status)
                if status in (401, 403):
                    message = (
                        "Gemini rejected the configured API credentials or permissions (HTTP %s)."
                        % status
                    )
                elif status == 429:
                    message = "Gemini rate limit or quota reached (HTTP 429). Try again later or check the Google AI project quota."
                elif status == 400:
                    message = "Gemini rejected the request (HTTP 400). Check the configured model and analysis prompt."
                elif status == 503:
                    message = "Gemini is temporarily unavailable (HTTP 503). Wait briefly and retry."
                elif status >= 500:
                    message = f"Gemini returned a server error (HTTP {status}). Retry once; if it persists, check Google's API status."
                else:
                    message = f"Gemini request failed with HTTP status {status}."
                raise GeminiAPIError(message) from exc
            except httpx.TimeoutException as exc:
                logger.warning("Gemini API request timed out.")
                raise GeminiAPIError(
                    "Gemini did not respond before the request timed out."
                ) from exc
            except httpx.RequestError as exc:
                logger.warning(
                    "Gemini API could not be reached (%s).", type(exc).__name__
                )
                raise GeminiAPIError(
                    "Gemini could not be reached. Check backend network access and retry."
                ) from exc
            except ValueError as exc:
                logger.warning("Gemini returned a non-JSON response.")
                raise GeminiAPIError("Gemini returned an unreadable response.") from exc
            except Exception as exc:
                logger.exception("Unexpected Gemini provider failure.")
                raise GeminiAPIError("Gemini returned an unexpected response.") from exc

        candidates = data.get("candidates") or []
        parts = (
            (candidates[0].get("content") or {}).get("parts") or []
            if candidates
            else []
        )
        content = "".join(
            part.get("text", "") for part in parts if isinstance(part, dict)
        )
        if not content.strip():
            finish_reason = candidates[0].get("finishReason") if candidates else None
            logger.warning(
                "Gemini response had no text candidate (finish reason: %s).",
                finish_reason,
            )
            raise GeminiAPIError(
                "Gemini did not return analysis text. Check the prompt and model response limits."
            )

        usage = data.get("usageMetadata") or {}
        return {
            "content": content,
            "model": data.get("modelVersion") or effective_model,
            "tokens_used": usage.get("totalTokenCount", 0),
            "duration_ms": int((time.monotonic() - start) * 1000),
        }
