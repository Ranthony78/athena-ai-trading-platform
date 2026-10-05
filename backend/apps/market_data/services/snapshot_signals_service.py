"""
Signals derived from stored option snapshots: OI change, volume spike,
spread tightening and IV velocity at the money.

Each signal is None ("not evaluable") when the snapshot history cannot
support it: too few snapshots, no baseline near the requested window, stale
data, or missing bid/ask. History only exists from the day snapshots were
first collected, so on a fresh deploy most of these are None for a while.
That is intended; nothing is estimated to fill the gap.

The calculators are pure functions over lists of points
({"t", "ltp", "bid", "ask", "volume", "oi"}, oldest first) so they can be
tested exactly. `SnapshotSignalsService.compute` does the database work.
"""

import logging
import statistics
from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from django.utils import timezone

from . import black76

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

WINDOW_MINUTES = 15  # look-back for OI change, spread and IV velocity
BASELINE_TOLERANCE = 0.4  # baseline may be off by this share of the window
MAX_AGE_MINUTES = 15  # latest snapshot older than this is stale
MIN_VOLUME_HISTORY = 5  # prior intervals needed for a volume baseline
LOOKBACK_HOURS = 8
RISK_FREE_RATE = 0.06
EXPIRY_CLOSE = time(15, 30)


def baseline_point(points: list[dict], window_minutes: int = WINDOW_MINUTES):
    """The point closest to `window_minutes` before the latest, within tolerance."""
    if len(points) < 2:
        return None
    latest = points[-1]
    target = latest["t"] - timedelta(minutes=window_minutes)
    tolerance = timedelta(minutes=window_minutes * BASELINE_TOLERANCE)
    candidates = [p for p in points[:-1] if abs(p["t"] - target) <= tolerance]
    return min(candidates, key=lambda p: abs(p["t"] - target)) if candidates else None


def oi_change(
    points: list[dict], window_minutes: int = WINDOW_MINUTES
) -> Optional[dict]:
    """Open-interest change over the window, in contracts and percent."""
    base = baseline_point(points, window_minutes)
    if base is None or not base.get("oi"):
        return None
    latest = points[-1]
    change = latest["oi"] - base["oi"]
    return {
        "change": change,
        "change_pct": round(change / base["oi"] * 100, 2),
        "window_minutes": window_minutes,
    }


def volume_spike(points: list[dict]) -> Optional[dict]:
    """
    Latest interval's traded volume against the median of earlier intervals
    the same day. Volume is cumulative, so intervals are differences; a drop
    (new day) restarts the series.
    """
    deltas = []
    for previous, current in zip(points, points[1:]):
        if current["t"].astimezone(IST).date() != previous["t"].astimezone(IST).date():
            deltas = []
            continue
        step = current["volume"] - previous["volume"]
        if step < 0:
            deltas = []
            continue
        deltas.append(step)
    if len(deltas) < MIN_VOLUME_HISTORY + 1:
        return None
    latest, history = deltas[-1], deltas[:-1]
    median = statistics.median(history)
    if median <= 0:
        return None
    return {
        "latest_interval_volume": latest,
        "median_interval_volume": median,
        "ratio": round(latest / median, 2),
    }


def _spread_pct(point: dict) -> Optional[float]:
    bid, ask = point.get("bid"), point.get("ask")
    if not bid or not ask or bid <= 0 or ask < bid:
        return None
    return (ask - bid) / ((ask + bid) / 2) * 100


def spread_tightening(
    points: list[dict], window_minutes: int = WINDOW_MINUTES
) -> Optional[dict]:
    """
    Bid-ask spread (percent of mid) now versus at the baseline. A negative
    change means the spread has tightened.
    """
    base = baseline_point(points, window_minutes)
    if base is None:
        return None
    now_pct, then_pct = _spread_pct(points[-1]), _spread_pct(base)
    if now_pct is None or then_pct is None or then_pct == 0:
        return None
    return {
        "spread_pct_now": round(now_pct, 3),
        "spread_pct_before": round(then_pct, 3),
        "change_pct": round((now_pct - then_pct) / then_pct * 100, 1),
        "tightening": now_pct < then_pct,
    }


def iv_velocity(
    iv_points: list[dict], window_minutes: int = WINDOW_MINUTES
) -> Optional[dict]:
    """
    Change in at-the-money IV (volatility points) per `window_minutes`.
    Points are {"t", "iv"} with iv in percent, oldest first.
    """
    base = baseline_point(iv_points, window_minutes)
    if base is None:
        return None
    latest = iv_points[-1]
    elapsed = (latest["t"] - base["t"]).total_seconds() / 60
    if elapsed <= 0:
        return None
    per_window = (latest["iv"] - base["iv"]) / elapsed * window_minutes
    return {
        "iv_now": round(latest["iv"], 2),
        "iv_before": round(base["iv"], 2),
        "change_per_window": round(per_window, 2),
        "window_minutes": window_minutes,
    }


def _years_to_expiry(expiry, at: datetime) -> float:
    close = datetime.combine(expiry, EXPIRY_CLOSE, tzinfo=IST)
    seconds = (close - at.astimezone(IST)).total_seconds()
    return max(seconds / (365 * 24 * 3600), 1 / (365 * 24))


def valuation_time(quote_timestamp, now: Optional[datetime] = None) -> datetime:
    """
    The moment the quoted option prices belong to, for time-to-expiry.

    Live, that is the quote's own time. After the close Zerodha keeps
    stamping quotes later in the evening, but the prices are still the
    15:30 closing prices, so the time is capped at that session's 15:30 IST.
    Valuing a 15:30 price as if it were quoted at 02:00 next morning
    shrinks the time left and inflates implied volatility and theta.
    Unparseable or future timestamps fall back to `now`.
    """
    now = now or timezone.now()
    at = quote_timestamp
    if isinstance(at, str):
        try:
            at = datetime.fromisoformat(at.replace("Z", "+00:00"))
        except ValueError:
            at = None
    if not isinstance(at, datetime):
        return now
    if at.tzinfo is None:
        at = at.replace(tzinfo=IST)  # Kite timestamps are naive IST
    if at > now + timedelta(minutes=1):
        return now
    local = at.astimezone(IST)
    close = datetime.combine(local.date(), EXPIRY_CLOSE, tzinfo=IST)
    return min(local, close)


class SnapshotSignalsService:

    @classmethod
    def compute(cls, underlying: str, now: Optional[datetime] = None) -> dict:
        """
        Signals for the at-the-money call and put of the nearest expiry, from
        the snapshots of the last few hours. Always returns every key; values
        are None when not evaluable.
        """
        from ..models import OptionSnapshot

        now = now or timezone.now()
        result = {
            "snapshots": 0,
            "latest_at": None,
            "expiry": None,
            "atm_strike": None,
            "oi_change": {"CE": None, "PE": None},
            "volume_spike": {"CE": None, "PE": None},
            "spread_tightening": {"CE": None, "PE": None},
            "iv_velocity": None,
        }
        rows = list(
            OptionSnapshot.objects.filter(
                underlying=underlying,
                captured_at__gte=now - timedelta(hours=LOOKBACK_HOURS),
                captured_at__lte=now,
                instrument__expiry__gte=now.astimezone(IST).date(),
            )
            .select_related("instrument")
            .order_by("captured_at")
        )
        if not rows:
            return result

        expiry = min(r.instrument.expiry for r in rows)
        rows = [r for r in rows if r.instrument.expiry == expiry]
        times = sorted({r.captured_at for r in rows})
        latest_at = times[-1]
        result.update(snapshots=len(times), latest_at=latest_at.isoformat())
        result["expiry"] = expiry.isoformat()
        if now - latest_at > timedelta(minutes=MAX_AGE_MINUTES):
            return result  # stale: every signal stays not evaluable

        latest_rows = [r for r in rows if r.captured_at == latest_at]
        spot = float(latest_rows[0].spot)
        strikes = {
            float(r.instrument.strike) for r in latest_rows if r.instrument.strike
        }
        if not strikes:
            return result
        atm = min(strikes, key=lambda strike: abs(strike - spot))
        result["atm_strike"] = atm

        for side in ("CE", "PE"):
            points = [
                {
                    "t": r.captured_at,
                    "ltp": float(r.ltp),
                    "bid": float(r.bid) if r.bid else None,
                    "ask": float(r.ask) if r.ask else None,
                    "volume": r.volume,
                    "oi": r.oi,
                }
                for r in rows
                if r.instrument.option_type == side
                and r.instrument.strike is not None
                and float(r.instrument.strike) == atm
            ]
            result["oi_change"][side] = oi_change(points)
            result["volume_spike"][side] = volume_spike(points)
            result["spread_tightening"][side] = spread_tightening(points)

        result["iv_velocity"] = iv_velocity(
            cls._atm_iv_series(rows, times, atm, expiry)
        )
        return result

    @staticmethod
    def _atm_iv_series(rows, times, atm, expiry) -> list[dict]:
        """ATM IV (call/put average, percent) at each snapshot time."""
        by_time: dict[datetime, list] = {}
        for r in rows:
            by_time.setdefault(r.captured_at, []).append(r)

        series = []
        for at in times:
            group = by_time[at]
            spot = float(group[0].spot)
            t = _years_to_expiry(expiry, at)
            chain = [
                {
                    "strike": float(r.instrument.strike),
                    "option_type": r.instrument.option_type,
                    "ltp": float(r.ltp),
                }
                for r in group
                if r.instrument.strike is not None
            ]
            forward = black76.parity_forward(chain, spot, t, RISK_FREE_RATE)
            if not forward:
                continue
            ivs = [
                black76.implied_vol(
                    c["ltp"], forward, atm, t, RISK_FREE_RATE, c["option_type"]
                )
                for c in chain
                if c["strike"] == atm
            ]
            ivs = [iv for iv in ivs if iv is not None]
            if ivs:
                series.append({"t": at, "iv": sum(ivs) / len(ivs) * 100})
        return series
