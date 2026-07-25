import json
import logging
import re
import time

from ..providers.ai_provider_factory import AIProviderFactory

logger = logging.getLogger(__name__)


class AIService:
    """
    Core AI service — sends prompts and parses responses.
    """

    def __init__(self) -> None:
        self.provider = AIProviderFactory.get_provider()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict:
        """
        Send a prompt to the AI provider and return the response.

        Returns:
            {
                "content": str,
                "model": str,
                "tokens_used": int,
                "duration_ms": int,
                "parsed": dict,
            }
        """
        result = self.provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        result["parsed"] = self._parse_json_block(result["content"])
        return result

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_block(content: str) -> dict:
        """
        Extract and parse the JSON block from AI response.
        Looks for ```json ... ``` block.
        """
        try:
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, content, re.DOTALL)

            if match:
                json_str = match.group(1).strip()
                return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI JSON block: {e}")
        except Exception as e:
            logger.error(f"AI response parse error: {e}")

        return {}