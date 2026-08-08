import logging

from apps.zerodha.services.kite_service import KiteService

logger = logging.getLogger(__name__)


class ZerodhaService:
    """
    Market data service using Zerodha Kite.
    Provides market data operations via KiteService.
    Used by the live market engine when MARKET_PROVIDER = 'zerodha'.
    """

    def __init__(self, user) -> None:
        self.user = user
        self.kite = KiteService(user)

    def get_quote(self, symbol: str) -> dict:
        return self.kite.get_quote(symbol)

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        return self.kite.get_quotes(symbols)

    def get_historical(
        self,
        instrument_token: int,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[dict]:
        return self.kite.get_historical(
            instrument_token=instrument_token,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
        )

    def get_positions(self) -> dict:
        return self.kite.get_positions()

    def get_holdings(self) -> list[dict]:
        return self.kite.get_holdings()

    def get_orders(self) -> list[dict]:
        return self.kite.get_orders()

    def get_funds(self) -> dict:
        return self.kite.get_funds()