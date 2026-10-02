"""Moonshot Kimi provider, available when a user selects Kimi explicitly."""

import logging
import time

import httpx
from django.conf import settings

from .base_ai_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class KimiAPIError(Exception):
    """Raised when Kimi cannot return a usable completion."""


class KimiProvider(BaseAIProvider):
    API_URL = "https://api.moonshot.ai/v1/chat/completions"
    DEFAULT_MODEL = "kimi-k3"

    def __init__(self, api_key=None) -> None:
        self.api_key = (
            api_key if api_key is not None else getattr(settings, "KIMI_API_KEY", "")
        )
        self.default_model = getattr(settings, "KIMI_MODEL", self.DEFAULT_MODEL)
        if not self.api_key:
            raise ValueError("KIMI_API_KEY is not configured on the backend.")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict:
        effective_model = (
            model if model and model.startswith("kimi-") else self.default_model
        )
        payload = {
            "model": effective_model,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        start = time.monotonic()
        try:
            response = httpx.post(
                self.API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise KimiAPIError("Kimi returned an empty analysis response.")
            return {
                "content": content,
                "model": data.get("model", effective_model),
                "tokens_used": (data.get("usage") or {}).get("total_tokens", 0),
                "duration_ms": int((time.monotonic() - start) * 1000),
            }
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            logger.warning("Kimi API returned HTTP %s.", code)
            if code == 429:
                message = "Kimi rate limit or quota reached (HTTP 429). Check the Moonshot project quota."
            elif code in (401, 403):
                message = "Kimi rejected the configured API credentials or permissions."
            elif code >= 500:
                message = f"Kimi is temporarily unavailable (HTTP {code})."
            else:
                message = f"Kimi rejected the request (HTTP {code}); check the configured model and prompt."
            raise KimiAPIError(message) from exc
        except httpx.TimeoutException as exc:
            logger.warning("Kimi API request timed out.")
            raise KimiAPIError(
                "Kimi did not respond before the request timed out."
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("Kimi API could not be reached (%s).", type(exc).__name__)
            raise KimiAPIError(
                "Kimi could not be reached. Check backend network access and retry."
            ) from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Kimi returned an unreadable completion response.")
            raise KimiAPIError(
                "Kimi returned an unreadable analysis response."
            ) from exc
