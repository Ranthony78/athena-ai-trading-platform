"""
Selects a real, tradable ATM option contract for a directional signal.

This is the minimal slice of strike/expiry selection needed to attach
a real option contract to AISignal/StrategySignal records (Step 1's
option_instrument FK) — the foundation for real-premium outcome
tracking. A fuller strike/expiry picker (ITM/OTM preference, weekly
vs monthly choice, etc.) is a separate, later feature; this always
picks ATM + nearest available expiry, which is a reasonable, honest
default.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StrikeSelectionService:
    """
    Given a signal's direction, selects a real ATM CE/PE contract
    (nearest available expiry) from the live option chain.
    """

    @staticmethod
    def select_for_signal(symbol: str, direction: str, user) -> Optional[dict]:
        """
        Args:
            symbol: underlying symbol, e.g. "NIFTY"
            direction: "BUY" or "SELL" — anything else (NEUTRAL,
                NO_SETUP, WATCH) returns None, since there's no
                directional call to attach a contract to.
            user: required to fetch real option chain data.

        Returns:
            {
                "instrument_id": int,       # real Instrument.pk
                "trading_symbol": str,
                "strike": float,
                "option_type": "CE" | "PE",
                "expiry": str,
                "entry_premium": float,     # real LTP at selection time
            }
            or None if a contract can't be selected (no user, no
            option chain data, direction isn't BUY/SELL, etc.) —
            never fabricates a contract or a premium.
        """
        if direction not in ("BUY", "SELL"):
            return None
        if not user:
            return None

        option_type = "CE" if direction == "BUY" else "PE"

        try:
            from .option_chain_service import OptionChainService
            from ..repositories.instrument_repository import InstrumentRepository

            service = OptionChainService(user=user)
            summary = service.get_chain_summary(symbol)

            atm_strike = summary.get("atm_strike")
            expiry = summary.get("expiry")
            if not atm_strike or not expiry:
                return None

            chain = service.get_chain(symbol, expiry=expiry)
            row = next(
                (
                    r for r in chain
                    if r.get("strike") == atm_strike and r.get("option_type") == option_type
                ),
                None,
            )
            if not row or not row.get("ltp"):
                return None

            instrument = InstrumentRepository.get_by_trading_symbol(
                row["trading_symbol"]
            )
            if not instrument:
                logger.error(
                    f"StrikeSelectionService: option chain returned "
                    f"trading_symbol {row['trading_symbol']!r} but no "
                    f"matching Instrument row exists."
                )
                return None

            return {
                "instrument_id": instrument.id,
                "trading_symbol": row["trading_symbol"],
                "strike": atm_strike,
                "option_type": option_type,
                "expiry": expiry,
                "entry_premium": row["ltp"],
            }

        except Exception as e:
            logger.error(
                f"StrikeSelectionService error [{symbol}, {direction}]: {e}"
            )
            return None