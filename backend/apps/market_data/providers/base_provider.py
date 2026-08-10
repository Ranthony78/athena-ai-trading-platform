from abc import ABC, abstractmethod


class BaseMarketProvider(ABC):

    @abstractmethod
    def get_quote(self, symbol: str):
        pass

    @abstractmethod
    def get_quotes(self, symbols: list):
        pass

    @abstractmethod
    def get_historical_data(self, symbol: str, interval: str):
        pass

    @abstractmethod
    def get_option_chain(self, symbol: str):
        pass