"""
Core option calculations for the workspaces: the parity forward, Black-76
implied volatility, the synthetic straddle, required moves to break even,
straddle Greeks, the VIX-implied one-session move, realized volatility and
IV velocity.

`compute` is pure (everything is passed in), so it is exactly testable.
`CoreCalculationsService.build` gathers the inputs. Any figure that cannot
be supported by verified inputs is None; nothing is estimated.
"""

import logging
import math
import statistics
from datetime import date, datetime
from typing import Optional

from . import black76
from .snapshot_signals_service import RISK_FREE_RATE, _years_to_expiry

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252
TRADING_MINUTES_PER_DAY = 375  # 09:15 to 15:30
REALIZED_VOL_SESSIONS = 10
MIN_REALIZED_VOL_CLOSES = REALIZED_VOL_SESSIONS + 1


def _price(rows: list[dict], strike: float, option_type: str) -> Optional[float]:
    for row in rows:
        if (
            row.get("option_type") == option_type
            and row.get("strike") == strike
            and (row.get("ltp") or 0) > 0
        ):
            return float(row["ltp"])
    return None


def realized_vol(
    closes: list[float], sessions: int = REALIZED_VOL_SESSIONS
) -> Optional[float]:
    """Annualised close-to-close volatility (percent) over the last `sessions`."""
    if len(closes) < sessions + 1 or any(
        c is None or c <= 0 for c in closes[-(sessions + 1) :]
    ):
        return None
    window = closes[-(sessions + 1) :]
    returns = [math.log(b / a) for a, b in zip(window, window[1:])]
    return round(statistics.stdev(returns) * math.sqrt(TRADING_DAYS_PER_YEAR) * 100, 2)


def vix_session_move(spot: float, vix: Optional[float]) -> Optional[float]:
    """One-sigma move over a single session implied by India VIX, in index points."""
    if not spot or spot <= 0 or not vix or vix <= 0:
        return None
    return round(spot * (vix / 100) / math.sqrt(TRADING_DAYS_PER_YEAR), 1)


def compute(
    spot: Optional[float],
    atm_strike: Optional[float],
    expiry: Optional[date],
    now: datetime,
    rows: list[dict],
    vix: Optional[float] = None,
    daily_closes: Optional[list[float]] = None,
    iv_velocity: Optional[dict] = None,
) -> dict:
    result = {
        "spot": spot,
        "atm_strike": atm_strike,
        "expiry": expiry.isoformat() if expiry else None,
        "forward": None,
        "call_price": None,
        "put_price": None,
        "call_iv": None,
        "put_iv": None,
        "implied_vol": None,
        "straddle": None,
        "straddle_pct_of_spot": None,
        "required_move": {
            "call": None,
            "put": None,
            "straddle_up": None,
            "straddle_down": None,
        },
        "straddle_greeks": None,
        "vix_session_move": vix_session_move(spot, vix),
        "realized_vol": realized_vol(daily_closes or []),
        "realized_vol_sessions": REALIZED_VOL_SESSIONS,
        "iv_velocity": iv_velocity,
        "model": "black76",
    }
    if not spot or not atm_strike or not expiry:
        return result

    t = _years_to_expiry(expiry, now)
    forward = black76.parity_forward(rows, spot, t, RISK_FREE_RATE)
    call = _price(rows, atm_strike, "CE")
    put = _price(rows, atm_strike, "PE")
    result["call_price"], result["put_price"] = call, put

    # Required move: how far the index must travel for the premium to be
    # recovered at expiry (strike +/- premium, measured from spot).
    if call is not None:
        result["required_move"]["call"] = round(atm_strike + call - spot, 1)
    if put is not None:
        result["required_move"]["put"] = round(atm_strike - put - spot, 1)
    if call is not None and put is not None:
        straddle = call + put
        result["straddle"] = round(straddle, 2)
        result["straddle_pct_of_spot"] = round(straddle / spot * 100, 2)
        result["required_move"]["straddle_up"] = round(atm_strike + straddle - spot, 1)
        result["required_move"]["straddle_down"] = round(
            atm_strike - straddle - spot, 1
        )

    if not forward:
        return result
    result["forward"] = round(forward, 2)

    ivs = {}
    for side, premium in (("CE", call), ("PE", put)):
        if premium is not None:
            ivs[side] = black76.implied_vol(
                premium, forward, atm_strike, t, RISK_FREE_RATE, side
            )
    result["call_iv"] = round(ivs["CE"] * 100, 2) if ivs.get("CE") else None
    result["put_iv"] = round(ivs["PE"] * 100, 2) if ivs.get("PE") else None
    valid = [v for v in ivs.values() if v]
    if valid:
        result["implied_vol"] = round(sum(valid) / len(valid) * 100, 2)

    if ivs.get("CE") and ivs.get("PE"):
        call_g = black76.greeks(forward, atm_strike, t, RISK_FREE_RATE, ivs["CE"], "CE")
        put_g = black76.greeks(forward, atm_strike, t, RISK_FREE_RATE, ivs["PE"], "PE")
        if call_g and put_g:
            theta_day = call_g["theta"] + put_g["theta"]
            result["straddle_greeks"] = {
                "theta_per_day": round(theta_day, 2),
                "theta_per_15_min": round(
                    theta_day / (TRADING_MINUTES_PER_DAY / 15), 2
                ),
                "gamma": round(call_g["gamma"] + put_g["gamma"], 6),
                "vega_per_vol_point": round(call_g["vega"] + put_g["vega"], 2),
            }
    return result


def _parse_time(value) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


class CoreCalculationsService:

    @staticmethod
    def _daily_closes(symbol: str) -> list[float]:
        from ..repositories.candle_repository import CandleRepository
        from ..repositories.instrument_repository import InstrumentRepository

        instrument = InstrumentRepository.get_by_symbol(symbol)
        if not instrument:
            return []
        candles = CandleRepository.get_by_instrument_and_timeframe(
            instrument, "1d", limit=REALIZED_VOL_SESSIONS + 5
        )
        return [float(c.close) for c in reversed(list(candles))]

    @staticmethod
    def _iv_velocity(symbol: str) -> Optional[dict]:
        from .snapshot_signals_service import SnapshotSignalsService

        try:
            return SnapshotSignalsService.compute(symbol)["iv_velocity"]
        except Exception as e:
            logger.error(f"CoreCalculations IV velocity error: {e}")
            return None

    @classmethod
    def from_context(
        cls, symbol: str, options: Optional[dict], vix: Optional[float]
    ) -> Optional[dict]:
        """
        Same figures as build(), from option data already fetched for the
        analysis prompt (its `core_rows`), so no second chain request is made.
        """
        from django.utils import timezone

        if not options or not options.get("core_rows") or not options.get("expiry"):
            return None
        return compute(
            spot=options.get("spot_price"),
            atm_strike=options.get("atm_strike"),
            expiry=date.fromisoformat(str(options["expiry"])),
            now=_parse_time(options.get("valuation_time")) or timezone.now(),
            rows=options["core_rows"],
            vix=vix,
            daily_closes=cls._daily_closes(symbol),
            iv_velocity=cls._iv_velocity(symbol),
        )

    @classmethod
    def build(cls, symbol: str, user) -> Optional[dict]:
        """Inputs from the live chain, VIX quote, daily candles and snapshots."""
        from django.utils import timezone

        from .market_service import MarketService
        from .option_chain_service import OptionChainService

        if not user:
            return None
        service = OptionChainService(user=user)
        summary = service.get_chain_summary(symbol)
        expiry_text, strike = summary.get("expiry"), summary.get("atm_strike")
        if not expiry_text or not strike:
            return None
        rows = service.get_chain(symbol, expiry=expiry_text)

        vix_quote = MarketService(user=user).quote("VIX") or {}
        try:
            vix = float(vix_quote.get("ltp"))
        except (TypeError, ValueError):
            vix = None

        return compute(
            spot=summary.get("spot_price"),
            atm_strike=strike,
            expiry=date.fromisoformat(str(expiry_text)),
            # Same clock as the chain's own IV, so both sections agree.
            now=getattr(service, "valuation_time", None) or timezone.now(),
            rows=rows,
            vix=vix,
            daily_closes=cls._daily_closes(symbol),
            iv_velocity=cls._iv_velocity(symbol),
        )
