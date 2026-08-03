from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI providers.
    Enforces a consistent interface across Claude, GPT, and mock.
    """

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict:
        """
        Send a completion request to the AI provider.

        Returns:
            {
                "content": str,       # AI response text
                "model": str,         # model used
                "tokens_used": int,   # total tokens consumed
                "duration_ms": int,   # response time in ms
            }
        """
        pass