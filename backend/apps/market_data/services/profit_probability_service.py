"""
Probability of profit for buying a call, a put or a long straddle at the
money, held for a chosen horizon.

For each structure we find the index move needed at the exit time for the
option(s) to be worth the entry premium plus costs (Black-76 repricing with
time decay and IV held at today's level, or shifted by a chosen number of
vol points). We then count how often past sessions moved at least that far,
entering at the same time of day and exiting after the same horizon. A
no-drift lognormal formula gives an independent cross-check.

These are historical frequencies under stated assumptions, not forecasts.
Nothing is shown without enough matching sessions. `compute` is pure.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from . import black76
from .snapshot_signals_service import RISK_FREE_RATE, _years_to_expiry

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
CANDLE_MINUTES = 15
SESSION_OPEN = 9 * 60 + 15
SESSION_CLOSE = 15 * 60 + 30
TRADING_MINUTES_PER_DAY = 375
TRADING_DAYS_PER_YEAR = 252
MIN_HISTORY_SESSIONS = 30
SESSIONS_TO_USE = 120
BROKERAGE_PER_ORDER = 20.0  # rupees, per leg, entry and exit each
IV_SHIFTS = (-2.0, 0.0, 2.0)  # vol points applied at the exit
CLEAR_EDGE_POINTS = 5.0  # lead needed over the runner-up to label a highest


def _cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _solve(fn, low: float, high: float) -> Optional[float]:
    """Bisection for fn(x) = 0 where fn(low) and fn(high) differ in sign."""
    f_low, f_high = fn(low), fn(high)
    if f_low is None or f_high is None or f_low == 0:
        return low if f_low == 0 else None
    if f_low * f_high > 0:
        return None
    for _ in range(80):
        mid = (low + high) / 2
        f_mid = fn(mid)
        if f_mid is None:
            return None
        if f_low * f_mid <= 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2


def breakeven_moves(
    forward: float,
    strike: float,
    t_entry: float,
    rate: float,
    call_iv: float,
    put_iv: float,
    call_premium: float,
    put_premium: float,
    horizon_minutes: int,
    cost_per_leg: float,
    iv_shift: float = 0.0,
) -> dict:
    """
    Index-point moves (in the forward) at the exit that make each structure
    worth its entry price plus costs. IVs are fractions (0.12 = 12%);
    `iv_shift` is in vol points applied to both at the exit.
    """
    elapsed = (horizon_minutes / TRADING_MINUTES_PER_DAY) / 365
    t_exit = t_entry - elapsed
    result = {"call": None, "put": None, "straddle_up": None, "straddle_down": None}
    if t_exit <= 0:
        return result
    ce_iv = max(call_iv + iv_shift / 100, 0.001)
    pe_iv = max(put_iv + iv_shift / 100, 0.001)

    def call_value(f):
        return black76.price(f, strike, t_exit, rate, ce_iv, "CE")

    def put_value(f):
        return black76.price(f, strike, t_exit, rate, pe_iv, "PE")

    call_target = call_premium + cost_per_leg
    put_target = put_premium + cost_per_leg
    straddle_target = call_premium + put_premium + 2 * cost_per_leg

    # Single legs are monotonic in the forward, so search the whole range: the
    # break-even can even be on the other side of today's forward when a rise
    # in IV already pays for the time decay.
    low, high = forward * 0.5, forward * 1.5
    up = _solve(lambda f: _minus(call_value(f), call_target), low, high)
    down = _solve(lambda f: _minus(put_value(f), put_target), low, high)

    def straddle_value(f):
        return _plus(call_value(f), put_value(f))

    # The straddle is U-shaped with its low point near the strike: one root on
    # each side. If even the low point pays, any move (or none) is profitable.
    at_strike = straddle_value(strike)
    s_up = s_down = None
    if at_strike is not None:
        if at_strike >= straddle_target:
            s_up = s_down = forward
        else:
            s_up = _solve(
                lambda f: _minus(straddle_value(f), straddle_target), strike, high
            )
            s_down = _solve(
                lambda f: _minus(straddle_value(f), straddle_target), low, strike
            )
    if up is not None:
        result["call"] = round(up - forward, 2)
    if down is not None:
        result["put"] = round(down - forward, 2)
    if s_up is not None:
        result["straddle_up"] = round(s_up - forward, 2)
    if s_down is not None:
        result["straddle_down"] = round(s_down - forward, 2)
    return result


def _minus(a, b):
    return None if a is None else a - b


def _plus(a, b):
    return None if a is None or b is None else a + b


def history_moves(
    candles: list[dict], anchor_minute: int, horizon_minutes: int
) -> list[float]:
    """
    Fractional index moves over the horizon, one per past session, entering
    at the open of the candle starting at `anchor_minute` and exiting at the
    close of the candle that ends `horizon_minutes` later. Sessions missing
    either candle are skipped.
    """
    last_start = anchor_minute + horizon_minutes - CANDLE_MINUTES
    if anchor_minute < SESSION_OPEN or last_start + CANDLE_MINUTES > SESSION_CLOSE:
        return []
    by_day: dict = defaultdict(dict)
    for candle in candles:
        local = candle["time"].astimezone(IST)
        by_day[local.date()][local.hour * 60 + local.minute] = candle
    moves = []
    for day in sorted(by_day)[-SESSIONS_TO_USE:]:
        entry = by_day[day].get(anchor_minute)
        exit_ = by_day[day].get(last_start)
        if entry and exit_ and entry["open"] > 0:
            moves.append(exit_["close"] / entry["open"] - 1)
    return moves


def model_probability(
    side: str, move_pct: float, iv: float, horizon_minutes: int
) -> Optional[float]:
    """No-drift lognormal chance of ending beyond the fractional move."""
    if not iv or iv <= 0 or move_pct is None or abs(move_pct) >= 1:
        return None
    sigma = iv * math.sqrt(
        horizon_minutes / (TRADING_MINUTES_PER_DAY * TRADING_DAYS_PER_YEAR)
    )
    drift = 0.5 * sigma * sigma
    if side == "up":
        return 1 - _cdf((math.log(1 + move_pct) + drift) / sigma)
    return _cdf((math.log(1 + move_pct) + drift) / sigma)


def _frequency(moves: list[float], hit) -> float:
    return sum(1 for m in moves if hit(m)) / len(moves) * 100


def compute(
    spot: float,
    core: dict,
    lot_size: Optional[int],
    now: datetime,
    horizon_minutes: int,
    anchor_minute: int,
    candles: list[dict],
    brokerage_per_order: float = BROKERAGE_PER_ORDER,
) -> dict:
    """`core` is the output of core_calculations_service.compute."""
    result = {
        "horizon_minutes": horizon_minutes,
        "anchor_minute": anchor_minute,
        "sessions": 0,
        "available": False,
        "reason": None,
        "iv": core.get("implied_vol"),
        "forward": core.get("forward"),
        "structures": {},
        "highest": None,
        "assumptions": [
            "IV is held at today's level (shown as a range for -2 / +2 vol points at exit).",
            f"Brokerage of ₹{brokerage_per_order:.0f} per order is included in the break-even.",
            "Past sessions are matched on time of day and horizon, not on market conditions.",
            "Historical frequency, not a forecast.",
        ],
    }
    needed = (
        "forward",
        "call_price",
        "put_price",
        "call_iv",
        "put_iv",
        "atm_strike",
        "expiry",
    )
    if any(core.get(key) in (None, "") for key in needed) or not spot or not lot_size:
        result["reason"] = "Needs a priced ATM call and put with implied volatility."
        return result

    moves = history_moves(candles, anchor_minute, horizon_minutes)
    result["sessions"] = len(moves)
    if not moves:
        result["reason"] = (
            "The horizon runs past the close or no matching candles are stored."
        )
        return result
    if len(moves) < MIN_HISTORY_SESSIONS:
        result["reason"] = (
            f"Only {len(moves)} matching sessions are stored; at least "
            f"{MIN_HISTORY_SESSIONS} are required."
        )
        return result

    from datetime import date as date_type

    expiry = date_type.fromisoformat(str(core["expiry"]))
    t_entry = _years_to_expiry(expiry, now)
    cost_per_leg = 2 * brokerage_per_order / lot_size
    call_iv, put_iv = core["call_iv"] / 100, core["put_iv"] / 100
    mean_iv = core["implied_vol"] / 100

    rows = {"call": [], "put": [], "straddle": []}
    detail = {}
    for shift in IV_SHIFTS:
        moves_needed = breakeven_moves(
            core["forward"],
            core["atm_strike"],
            t_entry,
            RISK_FREE_RATE,
            call_iv,
            put_iv,
            core["call_price"],
            core["put_price"],
            horizon_minutes,
            cost_per_leg,
            shift,
        )
        if shift == 0.0:
            detail = moves_needed
        c, p = moves_needed["call"], moves_needed["put"]
        su, sd = moves_needed["straddle_up"], moves_needed["straddle_down"]
        if c is not None:
            rows["call"].append(_frequency(moves, lambda m, b=c / spot: m >= b))
        if p is not None:
            rows["put"].append(_frequency(moves, lambda m, b=p / spot: m <= b))
        if su is not None and sd is not None:
            rows["straddle"].append(
                _frequency(moves, lambda m, u=su / spot, d=sd / spot: m >= u or m <= d)
            )

    def structure(name, premium, base_points, model):
        series = rows[name]
        return {
            "premium": round(premium, 2),
            "breakeven_points": base_points,
            "historical_pct": (
                round(series[IV_SHIFTS.index(0.0)], 1)
                if len(series) == len(IV_SHIFTS)
                else None
            ),
            "iv_range_pct": (
                [round(min(series), 1), round(max(series), 1)]
                if len(series) == len(IV_SHIFTS)
                else None
            ),
            "model_pct": None if model is None else round(model, 1),
        }

    def pct(points):
        return None if points is None else points / spot

    call_model = model_probability("up", pct(detail["call"]), mean_iv, horizon_minutes)
    put_model = model_probability("down", pct(detail["put"]), mean_iv, horizon_minutes)
    up_p = model_probability("up", pct(detail["straddle_up"]), mean_iv, horizon_minutes)
    down_p = model_probability(
        "down", pct(detail["straddle_down"]), mean_iv, horizon_minutes
    )
    straddle_model = None if up_p is None or down_p is None else up_p + down_p

    result["structures"] = {
        "call": structure(
            "call",
            core["call_price"],
            detail["call"],
            None if call_model is None else call_model * 100,
        ),
        "put": structure(
            "put",
            core["put_price"],
            detail["put"],
            None if put_model is None else put_model * 100,
        ),
        "straddle": {
            **structure(
                "straddle",
                core["call_price"] + core["put_price"],
                None,
                None if straddle_model is None else straddle_model * 100,
            ),
            "breakeven_up_points": detail["straddle_up"],
            "breakeven_down_points": detail["straddle_down"],
        },
    }
    result["available"] = True

    ranked = sorted(
        (
            (name, s["historical_pct"])
            for name, s in result["structures"].items()
            if s["historical_pct"] is not None
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    if len(ranked) >= 2 and ranked[0][1] - ranked[1][1] >= CLEAR_EDGE_POINTS:
        result["highest"] = ranked[0][0]
    return result


class ProfitProbabilityService:

    @classmethod
    def build(
        cls, symbol: str, user, horizon_minutes: int, mode: str = "LIVE"
    ) -> Optional[dict]:
        """Gather the live core figures and stored candles, then compute."""
        from .core_calculations_service import CoreCalculationsService

        core = CoreCalculationsService.build(symbol, user)
        return cls.from_core(symbol, core, horizon_minutes, mode)

    @classmethod
    def from_core(
        cls, symbol: str, core: Optional[dict], horizon_minutes: int, mode: str = "LIVE"
    ) -> Optional[dict]:
        """Same result from core figures already calculated elsewhere."""
        from django.utils import timezone

        from ..repositories.candle_repository import CandleRepository
        from ..repositories.instrument_repository import InstrumentRepository

        if not core or not core.get("spot"):
            return None

        instrument = InstrumentRepository.get_by_symbol(symbol)
        candles = []
        if instrument:
            rows = CandleRepository.get_by_instrument_and_timeframe(
                instrument, "15m", limit=SESSIONS_TO_USE * 26 + 26
            )
            candles = [
                {"time": r.candle_time, "open": float(r.open), "close": float(r.close)}
                for r in rows
            ]

        now = timezone.now()
        local = now.astimezone(IST)
        if mode == "NEXT_SESSION":
            anchor = SESSION_OPEN
        else:
            minute = local.hour * 60 + local.minute
            anchor = max(minute - minute % CANDLE_MINUTES, SESSION_OPEN)

        lot_size = cls._lot_size(symbol, core)
        return compute(
            core["spot"], core, lot_size, now, horizon_minutes, anchor, candles
        )

    @staticmethod
    def _lot_size(symbol: str, core: dict) -> Optional[int]:
        from ..models import Instrument

        strike, expiry = core.get("atm_strike"), core.get("expiry")
        contract = (
            Instrument.objects.filter(
                symbol=symbol, strike=strike, expiry=expiry, option_type="CE"
            )
            .only("lot_size")
            .first()
        )
        return contract.lot_size if contract else None
