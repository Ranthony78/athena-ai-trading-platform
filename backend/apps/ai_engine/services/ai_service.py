import json
import logging
import re

from ..providers.ai_provider_factory import AIProviderFactory
from .provider_credentials import ProviderCredentialService

logger = logging.getLogger(__name__)


class AIService:
    """
    Core AI service — sends prompts and parses responses.
    """

    def __init__(self, user=None) -> None:
        self.provider_config = ProviderCredentialService.resolve(user)
        self.provider = AIProviderFactory.get_provider(
            self.provider_config["provider"],
            api_key=self.provider_config["api_key"] or None,
        )
        self.provider_name = self.provider_config["provider"]

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4000,
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

        result["provider"] = self.provider_name
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
                value = json.loads(json_str)
            else:
                value = json.loads(content.strip())
            return value if isinstance(value, dict) else {}

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI JSON block: {e}")
        except Exception as e:
            logger.error(f"AI response parse error: {e}")

        return {}
