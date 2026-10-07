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
    def select_for_signal(
        symbol: str, direction: str, user, moneyness: str = "ATM"
    ) -> Optional[dict]:
        """
        Args:
            symbol: underlying symbol, e.g. "NIFTY"
            direction: "BUY" or "SELL" — anything else (NEUTRAL,
                NO_SETUP, WATCH) returns None, since there's no
                directional call to attach a contract to.
            moneyness: ATM, ITM, or OTM relative to the selected option side.
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
        moneyness = str(moneyness or "ATM").upper()
        if moneyness not in {"ATM", "ITM", "OTM"}:
            moneyness = "ATM"

        option_type = "CE" if direction == "BUY" else "PE"

        try:
            from ..repositories.instrument_repository import InstrumentRepository
            from .option_chain_service import OptionChainService

            symbol = InstrumentRepository.underlying_code(symbol)
            service = OptionChainService(user=user)
            summary = service.get_chain_summary(symbol)

            atm_strike = summary.get("atm_strike")
            expiry = summary.get("expiry")
            if not atm_strike or not expiry:
                return None

            chain = service.get_chain(symbol, expiry=expiry)
            candidates = [
                row
                for row in chain
                if row.get("option_type") == option_type
                and row.get("ltp")
                and (
                    (moneyness == "ATM" and row.get("strike") == atm_strike)
                    or (
                        moneyness == "ITM"
                        and (
                            row.get("strike") < atm_strike
                            if option_type == "CE"
                            else row.get("strike") > atm_strike
                        )
                    )
                    or (
                        moneyness == "OTM"
                        and (
                            row.get("strike") > atm_strike
                            if option_type == "CE"
                            else row.get("strike") < atm_strike
                        )
                    )
                )
            ]
            if moneyness == "ATM":
                row = candidates[0] if candidates else None
            elif moneyness == "ITM" and option_type == "CE":
                row = (
                    max(candidates, key=lambda item: item["strike"])
                    if candidates
                    else None
                )
            elif moneyness == "ITM":
                row = (
                    min(candidates, key=lambda item: item["strike"])
                    if candidates
                    else None
                )
            elif option_type == "CE":
                row = (
                    min(candidates, key=lambda item: item["strike"])
                    if candidates
                    else None
                )
            else:
                row = (
                    max(candidates, key=lambda item: item["strike"])
                    if candidates
                    else None
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
                "strike": row["strike"],
                "option_type": option_type,
                "moneyness": moneyness,
                "expiry": expiry,
                "entry_premium": row["ltp"],
                "lot_size": instrument.lot_size,
            }

        except Exception as e:
            logger.error(f"StrikeSelectionService error [{symbol}, {direction}]: {e}")
            return None

    # ------------------------------------------------------------------
    # Pure helpers over option-chain rows (no I/O). Rows are the dicts
    # returned by OptionChainService.get_chain().
    # ------------------------------------------------------------------

    @staticmethod
    def premium_matched_put(
        rows: list[dict], call_premium: float, max_gap_pct: float = 15.0
    ) -> Optional[dict]:
        """
        The PE whose premium is closest to `call_premium`, for building a
        premium-balanced pair against a call. None when no priced PE is
        within `max_gap_pct` percent of the call premium: a poor match is
        reported as absent rather than presented as balanced.
        """
        if not call_premium or call_premium <= 0:
            return None
        puts = [
            row
            for row in rows
            if row.get("option_type") == "PE" and (row.get("ltp") or 0) > 0
        ]
        if not puts:
            return None
        best = min(puts, key=lambda row: abs(row["ltp"] - call_premium))
        gap_pct = abs(best["ltp"] - call_premium) / call_premium * 100
        if gap_pct > max_gap_pct:
            return None
        return {**best, "premium_gap_pct": round(gap_pct, 2)}

    @staticmethod
    def oi_walls(rows: list[dict], spot: float) -> dict:
        """
        Highest open interest on each side of spot: the call wall above
        (resistance) and the put wall below (support). Either is None when
        that side has no OI; an OI of zero is not a wall.
        """
        if not spot or spot <= 0:
            return {"call_wall": None, "put_wall": None}

        def strongest(option_type, on_side):
            side = [
                row
                for row in rows
                if row.get("option_type") == option_type
                and (row.get("oi") or 0) > 0
                and on_side(row.get("strike") or 0)
            ]
            if not side:
                return None
            top = max(side, key=lambda row: row["oi"])
            return {"strike": top["strike"], "oi": top["oi"]}

        return {
            "call_wall": strongest("CE", lambda strike: strike >= spot),
            "put_wall": strongest("PE", lambda strike: 0 < strike <= spot),
        }
