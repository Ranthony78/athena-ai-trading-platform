from django.conf import settings

from .claude_provider import ClaudeProvider
from .mock_ai_provider import MockAIProvider


class AIProviderFactory:
    """
    Factory for AI providers.
    Switches between mock and Claude based on settings.
    """

    @staticmethod
    def get_provider():
        """
        Return the configured AI provider.

        Settings:
            AI_PROVIDER = "mock"    → MockAIProvider (default)
            AI_PROVIDER = "claude"  → ClaudeProvider
        """
        provider = getattr(settings, "AI_PROVIDER", "mock")

        if provider == "claude":
            return ClaudeProvider()

        return MockAIProvider()