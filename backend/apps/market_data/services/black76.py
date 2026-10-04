"""
Black-76 pricing, implied volatility and Greeks for European options on a
forward, plus the put-call-parity forward used to feed it.

Index options settle against the forward, not the spot, so pricing off a
forward implied by the option chain itself removes the need for a dividend
yield and most of the error from a fixed risk-free rate. Pure functions:
no I/O, and None (never a guess) when an input cannot support an answer.

Greeks are with respect to the forward. Vega is per 1 volatility point;
theta is per calendar day.
"""

import math
from typing import Optional

IV_LOWER_BOUND = 0.001  # 0.1%
IV_UPPER_BOUND = 5.0  # 500%
IV_TOLERANCE = 1e-6
IV_MAX_ITERATIONS = 100
FORWARD_STRIKES_EACH_SIDE = 2  # strikes around spot whose forwards are averaged


def _cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _is_call(option_type: str) -> bool:
    return option_type in ("CE", "CALL", "C")


def _valid(*values) -> bool:
    return all(
        isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in values
    )


def price(forward, strike, t, rate, vol, option_type) -> Optional[float]:
    """Black-76 option price; at zero vol, discounted intrinsic value."""
    if not _valid(forward, strike, t) or not math.isfinite(rate) or vol < 0:
        return None
    discount = math.exp(-rate * t)
    call = _is_call(option_type)
    if vol == 0:
        intrinsic = max(forward - strike, 0) if call else max(strike - forward, 0)
        return discount * intrinsic
    sd = vol * math.sqrt(t)
    d1 = (math.log(forward / strike) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    if call:
        return discount * (forward * _cdf(d1) - strike * _cdf(d2))
    return discount * (strike * _cdf(-d2) - forward * _cdf(-d1))


def implied_vol(market_price, forward, strike, t, rate, option_type) -> Optional[float]:
    """
    Bisection solve. None when the price is below discounted intrinsic
    value, outside what any volatility in range could produce (a bad or
    stale quote), or the inputs are unusable.
    """
    if not _valid(market_price, forward, strike, t) or not math.isfinite(rate):
        return None
    low, high = IV_LOWER_BOUND, IV_UPPER_BOUND
    price_low = price(forward, strike, t, rate, low, option_type)
    price_high = price(forward, strike, t, rate, high, option_type)
    if price_low is None or price_high is None:
        return None
    if not (price_low <= market_price <= price_high):
        return None

    mid = (low + high) / 2
    for _ in range(IV_MAX_ITERATIONS):
        mid = (low + high) / 2
        model = price(forward, strike, t, rate, mid, option_type)
        if abs(model - market_price) < IV_TOLERANCE:
            return mid
        if model < market_price:
            low = mid
        else:
            high = mid
    return mid


def greeks(forward, strike, t, rate, vol, option_type) -> Optional[dict]:
    """delta, gamma, theta (per day), vega (per vol point), all vs the forward."""
    if not _valid(forward, strike, t, vol) or not math.isfinite(rate):
        return None
    discount = math.exp(-rate * t)
    sqrt_t = math.sqrt(t)
    sd = vol * sqrt_t
    d1 = (math.log(forward / strike) + 0.5 * sd * sd) / sd
    pdf_d1 = _pdf(d1)

    model = price(forward, strike, t, rate, vol, option_type)
    delta = discount * (_cdf(d1) if _is_call(option_type) else _cdf(d1) - 1)
    gamma = discount * pdf_d1 / (forward * sd)
    vega = discount * forward * pdf_d1 * sqrt_t / 100
    theta = (rate * model - discount * forward * pdf_d1 * vol / (2 * sqrt_t)) / 365
    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}


def parity_forward(
    rows: list[dict], spot: float, t: float, rate: float
) -> Optional[float]:
    """
    Forward implied by put-call parity, F = K + e^{rT} (C - P), averaged
    over the few strikes nearest spot that have both a priced call and put.
    None when no such strike exists, so callers fall back rather than
    price off an unverified forward.
    """
    if not _valid(spot, t) or not math.isfinite(rate):
        return None
    by_strike: dict[float, dict] = {}
    for row in rows:
        ltp = row.get("ltp")
        strike = row.get("strike")
        option_type = row.get("option_type")
        if option_type not in ("CE", "PE") or not _valid(ltp, strike):
            continue
        by_strike.setdefault(strike, {})[option_type] = ltp

    paired = sorted(
        (k for k, v in by_strike.items() if "CE" in v and "PE" in v),
        key=lambda k: abs(k - spot),
    )[: FORWARD_STRIKES_EACH_SIDE * 2 + 1]
    if not paired:
        return None
    growth = math.exp(rate * t)
    forwards = [k + growth * (by_strike[k]["CE"] - by_strike[k]["PE"]) for k in paired]
    forwards = [f for f in forwards if f > 0]
    return sum(forwards) / len(forwards) if forwards else None
