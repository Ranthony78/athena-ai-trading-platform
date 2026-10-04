"""
Captures raw option-chain values around the money for history, and purges
old rows. Stores only real quotes: contracts with no usable price are
skipped, and nothing is stored without a valid underlying price.
"""

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from ..models import Instrument, OptionSnapshot

logger = logging.getLogger(__name__)

STRIKES_EACH_SIDE = 10
RETENTION_DAYS = 20


def _decimal(value) -> Optional[Decimal]:
    try:
        number = Decimal(str(value))
    except Exception:
        return None
    return number if number > 0 else None


class OptionSnapshotService:

    @classmethod
    def capture(
        cls, symbol: str, user, strikes_each_side: int = STRIKES_EACH_SIDE
    ) -> int:
        """Store the nearest expiry's ATM +/- N strikes; returns rows saved."""
        from .market_service import MarketService
        from .option_chain_service import OptionChainService

        service = OptionChainService(user=user)
        summary = service.get_chain_summary(symbol)
        expiry = summary.get("expiry")
        spot = _decimal(summary.get("spot_price"))
        if not expiry or spot is None:
            return 0

        rows = MarketService(user=user).option_chain(symbol, expiry=expiry)
        strikes = sorted({row["strike"] for row in rows if row.get("strike")})
        if not strikes:
            return 0
        atm_index = min(
            range(len(strikes)), key=lambda i: abs(strikes[i] - float(spot))
        )
        wanted = set(
            strikes[
                max(0, atm_index - strikes_each_side) : atm_index
                + strikes_each_side
                + 1
            ]
        )

        by_symbol = {
            i.trading_symbol: i
            for i in Instrument.objects.filter(
                trading_symbol__in=[r["trading_symbol"] for r in rows]
            )
        }
        now = timezone.now()
        batch = []
        for row in rows:
            instrument = by_symbol.get(row.get("trading_symbol"))
            ltp = _decimal(row.get("ltp"))
            if row.get("strike") not in wanted or instrument is None or ltp is None:
                continue
            batch.append(
                OptionSnapshot(
                    underlying=symbol,
                    instrument=instrument,
                    captured_at=now,
                    spot=spot,
                    ltp=ltp,
                    bid=_decimal(row.get("best_bid")),
                    ask=_decimal(row.get("best_ask")),
                    volume=int(row.get("volume") or 0),
                    oi=int(row.get("oi") or 0),
                )
            )
        OptionSnapshot.objects.bulk_create(batch)
        return len(batch)

    @staticmethod
    def purge(days: int = RETENTION_DAYS) -> int:
        deleted, _ = OptionSnapshot.objects.filter(
            captured_at__lt=timezone.now() - timedelta(days=days)
        ).delete()
        return deleted
