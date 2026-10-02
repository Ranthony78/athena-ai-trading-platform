from django.conf import settings

from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .kimi_provider import KimiProvider
from .mock_ai_provider import MockAIProvider


class AIProviderFactory:
    """
    Factory for AI providers.
    Switches between mock, Claude, Gemini, and Groq based on settings.
    """

    @staticmethod
    def get_provider(provider=None, api_key=None):
        """
        Return the configured AI provider.

        Settings:
            AI_PROVIDER = "mock"    → MockAIProvider
            AI_PROVIDER = "claude"  → ClaudeProvider
            AI_PROVIDER = "gemini"  → GeminiProvider
            AI_PROVIDER = "groq"    → GroqProvider (free-tier testing)
        """
        provider = provider or getattr(settings, "AI_PROVIDER", "mock")

        if provider == "claude":
            return ClaudeProvider(api_key=api_key)

        if provider == "groq":
            return GroqProvider(api_key=api_key)

        if provider == "kimi":
            return KimiProvider(api_key=api_key)

        if provider == "gemini":
            return GeminiProvider(api_key=api_key)

        if provider == "mock":
            return MockAIProvider()

        raise ValueError(
            f"Unsupported AI provider '{provider}'. Choose mock, claude, gemini, groq, or kimi."
        )
