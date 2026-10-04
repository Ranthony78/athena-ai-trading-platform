"""
Filter engine for buying ATM options: six strict filters, of which at least
four must pass. A filter that cannot be evaluated (missing data) or does
not apply (for example outside entry hours) counts as NOT passed; unknown
is never a pass.

Filters A, B and F follow the reference prompt's wording. C, D and E were
described by the reference only by name, so their thresholds below are
Athena's own proposals and are flagged as such in the output. All
thresholds live in `EngineParameters`.

`evaluate` is pure. `FilterEngineService.build` gathers the inputs. The
result is analysis only: it never places or prepares an order.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

PASS = "pass"
FAIL = "fail"
NOT_EVALUABLE = "not_evaluable"
NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class EngineParameters:
    # A: value of IV change per window must exceed this multiple of theta decay.
    iv_velocity_theta_multiple: float = 0.6
    # B: VIX-implied one-session move must be at least this multiple of the required move.
    expected_move_multiple: float = 0.9
    # C (proposed): ATM call or put open interest must change by at least this percent in the window.
    oi_change_pct: float = 5.0
    # D (proposed): realized volatility divided by implied volatility must be at least this.
    realized_implied_ratio: float = 0.9
    # E (proposed): each evaluable ATM leg's spread must have narrowed by at least this percent.
    spread_tightening_pct: float = 10.0
    # F: last entry time (IST).
    last_entry: time = time(14, 0)
    # Filters that must pass.
    min_passes: int = 4


PROPOSED = {"C", "D", "E"}  # thresholds chosen by Athena, not taken from the reference


def _filter(key, name, status, detail, rule):
    return {
        "key": key,
        "name": name,
        "status": status,
        "detail": detail,
        "rule": rule,
        "threshold_source": "proposed" if key in PROPOSED else "reference",
    }


def _filter_a(core, params):
    name = f"IV velocity > {params.iv_velocity_theta_multiple} × theta"
    rule = "The money value of the IV change over the window must exceed the theta decay over the same window, and IV must be rising."
    velocity = (core or {}).get("iv_velocity")
    greeks = (core or {}).get("straddle_greeks")
    if not velocity or not greeks:
        return _filter(
            "A",
            name,
            NOT_EVALUABLE,
            "IV history or Greeks are not available yet.",
            rule,
        )
    window = velocity["window_minutes"]
    iv_value = velocity["change_per_window"] * greeks["vega_per_vol_point"]
    theta_window = abs(greeks["theta_per_15_min"]) * window / 15
    needed = params.iv_velocity_theta_multiple * theta_window
    detail = (
        f"IV change {velocity['change_per_window']:+.2f} pts per {window} min is worth "
        f"{'-' if iv_value < 0 else '+'}₹{abs(iv_value):.2f}; theta over the same time is ₹{theta_window:.2f} "
        f"(needs more than ₹{needed:.2f})."
    )
    if iv_value > needed:
        return _filter("A", name, PASS, detail, rule)
    if velocity["change_per_window"] <= 0:
        detail += " IV is not rising, which hurts long options."
    return _filter("A", name, FAIL, detail, rule)


def _filter_b(core, params):
    name = f"Expected move ≥ {params.expected_move_multiple} × required"
    rule = "The VIX-implied one-session move must be at least this multiple of the move needed to break even. Passes if any structure qualifies."
    expected = (core or {}).get("vix_session_move")
    move = (core or {}).get("required_move") or {}
    legs = {
        "call": move.get("call"),
        "put": move.get("put"),
        "straddle": min(
            (
                abs(v)
                for v in (move.get("straddle_up"), move.get("straddle_down"))
                if v is not None
            ),
            default=None,
        ),
    }
    legs = {k: abs(v) for k, v in legs.items() if v is not None}
    if expected is None or not legs:
        return _filter(
            "B",
            name,
            NOT_EVALUABLE,
            "VIX or the required moves are not available.",
            rule,
        )
    passed = {k: expected >= params.expected_move_multiple * v for k, v in legs.items()}
    detail = f"Expected ±{expected:.0f} pts vs " + ", ".join(
        f"{k} needs {params.expected_move_multiple * v:.0f} ({'pass' if passed[k] else 'fail'})"
        for k, v in legs.items()
    )
    return _filter("B", name, PASS if any(passed.values()) else FAIL, detail, rule)


def _filter_c(signals, params):
    name = f"OI change ≥ {params.oi_change_pct:g}% at the money"
    rule = "Open interest at the ATM call or put must change by at least this percent over the window (a spike or an unwind both count). Threshold proposed by Athena."
    changes = (signals or {}).get("oi_change") or {}
    values = {
        side: (changes.get(side) or {}).get("change_pct") for side in ("CE", "PE")
    }
    known = {k: v for k, v in values.items() if v is not None}
    if not known:
        return _filter(
            "C", name, NOT_EVALUABLE, "Not enough stored option snapshots yet.", rule
        )
    detail = ", ".join(f"{k} {v:+.1f}%" for k, v in known.items())
    hit = any(abs(v) >= params.oi_change_pct for v in known.values())
    return _filter("C", name, PASS if hit else FAIL, detail, rule)


def _filter_d(core, params):
    name = f"Realized / implied volatility ≥ {params.realized_implied_ratio:g}"
    rule = "Long gamma only pays if the market moves about as much as the options price in. Threshold proposed by Athena."
    realized, implied = (core or {}).get("realized_vol"), (core or {}).get(
        "implied_vol"
    )
    if realized is None or not implied:
        return _filter(
            "D",
            name,
            NOT_EVALUABLE,
            "Realized or implied volatility is not available.",
            rule,
        )
    ratio = realized / implied
    detail = f"Realized {realized:.2f}% / implied {implied:.2f}% = {ratio:.2f}."
    return _filter(
        "D",
        name,
        PASS if ratio >= params.realized_implied_ratio else FAIL,
        detail,
        rule,
    )


def _filter_e(signals, params):
    name = f"Spread tightening ≥ {params.spread_tightening_pct:g}%"
    rule = "The bid-ask spread of each evaluable ATM leg must have narrowed by at least this percent over the window. Threshold proposed by Athena."
    legs = (signals or {}).get("spread_tightening") or {}
    known = {k: v for k, v in legs.items() if v}
    if not known:
        return _filter(
            "E",
            name,
            NOT_EVALUABLE,
            "Order-book depth or history is not available.",
            rule,
        )
    detail = ", ".join(f"{k} {v['change_pct']:+.1f}%" for k, v in known.items())
    ok = all(v["change_pct"] <= -params.spread_tightening_pct for v in known.values())
    return _filter("E", name, PASS if ok else FAIL, detail, rule)


def _filter_f(now, market_open, mode, params):
    name = f"Entry before {params.last_entry.strftime('%H:%M')} IST"
    rule = "New entries are only allowed before the last entry time, while the market is open."
    if mode == "NEXT_SESSION" or not market_open:
        return _filter(
            "F",
            name,
            NOT_APPLICABLE,
            "The market is closed or this is a next-session outlook.",
            rule,
        )
    local = now.astimezone(IST).time()
    detail = f"It is {local.strftime('%H:%M')} IST."
    return _filter("F", name, PASS if local < params.last_entry else FAIL, detail, rule)


def evaluate(
    core: Optional[dict],
    signals: Optional[dict],
    now: datetime,
    market_open: bool,
    mode: str = "LIVE",
    params: EngineParameters = EngineParameters(),
    profit_probability: Optional[dict] = None,
) -> dict:
    filters = [
        _filter_a(core, params),
        _filter_b(core, params),
        _filter_c(signals, params),
        _filter_d(core, params),
        _filter_e(signals, params),
        _filter_f(now, market_open, mode, params),
    ]
    passed = sum(1 for f in filters if f["status"] == PASS)
    met = passed >= params.min_passes
    highest = (profit_probability or {}).get("highest")

    if not met:
        verdict, text = (
            "NO_TRADE",
            f"No trade: {passed} of 6 filters passed; {params.min_passes} are required.",
        )
    elif highest:
        verdict, text = "CONDITIONS_MET", (
            f"Filters met ({passed} of 6). Past sessions favour the {highest} structure most; "
            "this is analysis, not an order."
        )
    else:
        verdict, text = "CONDITIONS_MET", (
            f"Filters met ({passed} of 6), but no structure has a clear historical lead."
        )
    return {
        "filters": filters,
        "passed": passed,
        "required": params.min_passes,
        "verdict": verdict,
        "verdict_text": text,
        "highest_structure": highest if met else None,
        "parameters": {
            **{k: v for k, v in asdict(params).items() if k != "last_entry"},
            "last_entry": params.last_entry.strftime("%H:%M"),
        },
        "note": (
            "Unknown or not-applicable filters count as not passed. Thresholds for C, D and E "
            "are Athena's proposals; A, B and F follow the reference."
        ),
    }


class FilterEngineService:

    @classmethod
    def build(
        cls, symbol: str, user, horizon_minutes: int, mode: str = "LIVE"
    ) -> Optional[dict]:
        """Filters, verdict and profit probabilities from one set of live inputs."""
        from django.utils import timezone

        from ..engine.market_state import MarketState
        from .core_calculations_service import CoreCalculationsService
        from .profit_probability_service import ProfitProbabilityService
        from .snapshot_signals_service import SnapshotSignalsService

        core = CoreCalculationsService.build(symbol, user)
        if not core:
            return None
        try:
            signals = SnapshotSignalsService.compute(symbol)
        except Exception as e:
            logger.error(f"FilterEngine snapshot signals error: {e}")
            signals = None
        try:
            probability = ProfitProbabilityService.from_core(
                symbol, core, horizon_minutes, mode
            )
        except Exception as e:
            logger.error(f"FilterEngine profit probability error: {e}")
            probability = None

        market_open = bool(MarketState.session_info().get("is_live"))
        result = evaluate(
            core,
            signals,
            timezone.now(),
            market_open,
            mode,
            profit_probability=probability,
        )
        return {
            "engine": result,
            "profit_probability": probability,
            "horizon_minutes": horizon_minutes,
            "mode": mode,
        }
