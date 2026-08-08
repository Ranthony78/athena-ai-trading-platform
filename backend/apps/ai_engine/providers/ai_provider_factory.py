from django.conf import settings

from .claude_provider import ClaudeProvider
from .groq_provider import GroqProvider
from .mock_ai_provider import MockAIProvider


class AIProviderFactory:
    """
    Factory for AI providers.
    Switches between mock, Claude, and Groq based on settings.
    """

    @staticmethod
    def get_provider():
        """
        Return the configured AI provider.

        Settings:
            AI_PROVIDER = "mock"    → MockAIProvider (default)
            AI_PROVIDER = "claude"  → ClaudeProvider
            AI_PROVIDER = "groq"    → GroqProvider (free-tier testing)
        """
        provider = getattr(settings, "AI_PROVIDER", "mock")

        if provider == "claude":
            return ClaudeProvider()

        if provider == "groq":
            return GroqProvider()

        return MockAIProvider()