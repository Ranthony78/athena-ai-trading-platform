"""
Front-month futures contracts and their live quote facts (VWAP, volume,
open interest). Contracts are resolved from the Instrument table, never
from a constructed symbol. Mock data is never used: with a non-Zerodha
provider every method returns None.
"""

from typing import Optional

from django.conf import settings
from django.utils import timezone

from ..models import Instrument


class FuturesService:

    @staticmethod
    def front_contract(symbols, exchange: str = "NFO") -> Optional[Instrument]:
        """Nearest unexpired active FUT contract for any of `symbols`."""
        if isinstance(symbols, str):
            symbols = (symbols,)
        return (
            Instrument.objects.filter(
                symbol__in=symbols,
                exchange=exchange,
                instrument_type="FUT",
                expiry__gte=timezone.localdate(),
                is_active=True,
            )
            .order_by("expiry")
            .first()
        )

    @classmethod
    def snapshot(cls, symbol: str, user) -> Optional[dict]:
        """
        {contract, expiry, ltp, vwap, volume, oi, high, low, prev_close}
        for the front-month future, or None when it cannot be verified.
        """
        if not user or getattr(settings, "MARKET_PROVIDER", "mock") != "zerodha":
            return None
        contract = cls.front_contract(symbol.upper())
        if not contract:
            return None

        from .market_service import MarketService

        quote = MarketService(user=user).quote(contract.trading_symbol)
        try:
            ltp = float(quote.get("ltp"))
        except (AttributeError, TypeError, ValueError):
            return None
        if ltp <= 0:
            return None

        def number(key):
            try:
                value = float(quote.get(key))
            except (TypeError, ValueError):
                return None
            return value if value > 0 else None

        return {
            "contract": contract.trading_symbol,
            "expiry": contract.expiry.isoformat(),
            "ltp": ltp,
            "vwap": number("average_price"),
            "volume": int(quote.get("volume") or 0),
            "oi": int(quote.get("oi") or 0),
            "high": number("high"),
            "low": number("low"),
            "prev_close": number("close"),
        }
