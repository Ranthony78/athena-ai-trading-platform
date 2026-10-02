from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .mock_provider import MockMarketProvider
from .zerodha_provider import ZerodhaProvider


class ProviderFactory:

    @staticmethod
    def get_provider(user=None):
        """
        Return the configured market data provider.

        user is only required when MARKET_PROVIDER="zerodha" — the
        mock provider doesn't need one. Pass it through wherever a
        request.user (or account.user) is available.
        """
        provider = getattr(settings, "MARKET_PROVIDER", "mock")

        if provider == "zerodha":
            return ZerodhaProvider(user=user)

        if provider == "mock":
            return MockMarketProvider()

        raise ImproperlyConfigured("MARKET_PROVIDER must be 'mock' or 'zerodha'.")
