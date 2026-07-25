from django.conf import settings

from .mock_provider import MockMarketProvider
from .zerodha_provider import ZerodhaProvider


class ProviderFactory:

    @staticmethod
    def get_provider():

        provider = getattr(settings, "MARKET_PROVIDER", "mock")

        if provider == "zerodha":
            return ZerodhaProvider()

        return MockMarketProvider()