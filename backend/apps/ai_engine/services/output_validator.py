"""
Catches the specific hallucination pattern found in production: the model
citing a risk factor (e.g. "VIX elevated") for data that was never in its
input context, or restating a status field (session) differently from
what it was actually given — both direct violations of the system
prompt's "never fabricate, report NA" rule that the prompt instruction
alone didn't reliably prevent.

Scope, deliberately: this validates against a known list of terms whose
groundedness depends on what was actually fetched for THIS call — not a
blanket static list. VIX in particular is now sometimes real data (see
PromptService._safe_get_vix), so it's only flagged as fabricated when
this specific call's market_context shows no VIX was returned. This is
NOT a general-purpose fact-checker; it doesn't try to verify every claim
against every context field. It closes the specific hole that was found
and stays correct as more real data sources get wired in over time.
"""

import logging
import math
import re
from datetime import time as datetime_time
from typing import Optional

logger = logging.getLogger(__name__)


class OutputValidator:
    """
    Validates AI-generated analysis output against the market_context it
    was actually built from. Never raises — a validation failure should
    degrade to "couldn't clean this" with a logged warning, not crash the
    analysis pipeline.
    """

    # term -> function(market_context) -> True if grounded for THIS call.
    # VIX is conditional: it's grounded when PromptService actually
    # fetched a real quote for it, ungrounded (and safe to strip) when
    # that fetch failed or wasn't attempted (e.g. no user context). The
    # others are unconditionally ungrounded until Athena has a real data
    # source for them (see PromptService's docstring for current status).
    CONDITIONAL_TERMS = {
        "vix": lambda ctx: bool((ctx or {}).get("vix")),
        "fii": lambda ctx: False,
        "dii": lambda ctx: False,
        "market breadth": lambda ctx: bool((ctx or {}).get("breadth")),
        "sentiment": lambda ctx: bool((ctx or {}).get("news_sentiment")),
    }

    REASONS = {
        "vix": "India VIX data was not available for this specific analysis call (no live quote returned).",
        "fii": "FII flow data is not available via Kite Connect.",
        "dii": "DII flow data is not available via Kite Connect.",
        "market breadth": "Market breadth data was not available for this specific analysis call.",
        "sentiment": "News sentiment data was not available for this specific analysis call (Marketaux key unset or request failed).",
    }

    @classmethod
    def validate(cls, parsed: dict, market_context: dict, raw_content: str) -> dict:
        """
        Returns:
            {
                "parsed": <cleaned copy of parsed>,
                "warnings": [<str>, ...],
            }
        """
        warnings: list[str] = []
        cleaned = dict(parsed) if isinstance(parsed, dict) else {}
        cls._structure(cleaned, market_context, warnings)

        cleaned["risks"], risk_warnings = cls._clean_risks(
            cleaned.get("risks") or [], market_context
        )
        warnings.extend(risk_warnings)

        probability_warning = cls._enforce_historical_probability(
            cleaned, market_context
        )
        if probability_warning:
            warnings.append(probability_warning)

        session_warning = cls._check_session_claim(market_context, raw_content)
        if session_warning:
            warnings.append(session_warning)

        return {"parsed": cleaned, "warnings": warnings}

    @staticmethod
    def _structure(output, context, warnings):
        """Restrict structured fields; qualitative prose is still AI interpretation."""
        context = context or {}
        signal = str(output.get("signal", "NO_SETUP")).upper()
        reason = output.get("no_trade_reason")
        analysis_mode = context.get("analysis_mode", "LIVE")
        live_context_unavailable = False
        if analysis_mode == "NEXT_SESSION":
            signal = "NO_SETUP"
            reason = "Next-session outlook only: scenarios are conditional and cannot authorize a current entry or paper trade."
            if str(output.get("signal", "")).upper() in ("BUY", "SELL"):
                warnings.append(
                    "Next-session outlook cannot emit an actionable BUY/SELL signal; normalized to No Trade."
                )
            if context.get("error"):
                output["market_view"] = "UNCERTAIN"
                output["scenarios"] = {
                    key: "Unavailable because required market candle data could not be loaded."
                    for key in ("bullish", "bearish", "sideways")
                }
                output["confidence"] = 0
                output["missing_information"] = [context["error"]]
        elif signal not in ("BUY", "SELL"):
            signal = "NO_SETUP"
            reason = (
                reason
                if isinstance(reason, str) and reason.strip()
                else "The evidence does not support a clear directional trade."
            )
        quote = context.get("quote") or {}
        from apps.paper_trading.services.broker_simulator import BrokerSimulator

        if analysis_mode != "NEXT_SESSION":
            if (
                context.get("error")
                or not quote
                or context.get("quote_source") != "ZERODHA"
                or BrokerSimulator._quote_is_stale(quote.get("timestamp"))
            ):
                signal, reason = (
                    "NO_SETUP",
                    "Current verified price evidence is missing or stale. Refresh market data before considering a trade.",
                )
                live_context_unavailable = True
            elif (context.get("session") or {}).get("is_live") is not True:
                session = context.get("session") or {}
                if session.get("is_live") is False:
                    signal, reason = (
                        "NO_SETUP",
                        "The market is closed. LIVE mode does not create a next-session outlook; select NEXT_SESSION for conditional planning.",
                    )
                else:
                    signal, reason = (
                        "NO_SETUP",
                        "Session status is unavailable. Refresh market/session data before requesting a live analysis.",
                    )
                live_context_unavailable = True
            else:
                try:
                    current_time = datetime_time.fromisoformat(
                        str(context["session"]["time"])
                    )
                    if current_time >= datetime_time(14, 0):
                        signal, reason = (
                            "NO_SETUP",
                            "No new setup is eligible at or after 14:00 IST.",
                        )
                except (KeyError, TypeError, ValueError):
                    signal, reason = (
                        "NO_SETUP",
                        "Session time is unavailable; setup timing cannot be verified.",
                    )
        else:
            output["target"] = None
            output["stop_loss"] = None
        if signal != output.get("signal"):
            warnings.append(
                "Decision normalized to No Trade where evidence or session conditions do not support an entry."
            )
        output["signal"], output["no_trade_reason"] = signal, (
            reason if signal == "NO_SETUP" else None
        )
        if live_context_unavailable:
            output["market_view"] = "UNCERTAIN"
            output["scenarios"] = {
                key: (
                    "Unavailable in LIVE mode while the market is closed; select NEXT_SESSION for a conditional outlook."
                    if (context.get("session") or {}).get("is_live") is False
                    else "Unavailable because fresh, verified live price and session evidence is missing."
                )
                for key in ("bullish", "bearish", "sideways")
            }
            output["confidence"] = 0
            missing = output.get("missing_information")
            missing = list(missing) if isinstance(missing, list) else []
            missing.append(
                "LIVE analysis requires an open session and fresh verified price data; use NEXT_SESSION explicitly for after-market planning."
            )
            output["missing_information"] = missing
        moneyness = str(output.get("option_moneyness") or "").upper()
        if signal in ("BUY", "SELL"):
            output["option_moneyness"] = (
                moneyness if moneyness in {"ATM", "ITM", "OTM"} else "ATM"
            )
            selection_reason = output.get("option_selection_reason")
            output["option_selection_reason"] = (
                selection_reason[:500]
                if isinstance(selection_reason, str) and selection_reason.strip()
                else "No distinct moneyness preference was supported; using the nearest listed ATM contract."
            )
        else:
            output["option_moneyness"] = None
            output["option_selection_reason"] = None
            if signal == "NO_SETUP":
                output["target"] = None
                output["stop_loss"] = None
        for key in (
            "risks",
            "supporting_evidence",
            "conflicting_evidence",
            "invalidation_conditions",
            "missing_information",
        ):
            value = output.get(key)
            output[key] = (
                [s[:1500] for s in value if isinstance(s, str)][:20]
                if isinstance(value, list)
                else []
            )
        view = output.get("market_view")
        output["market_view"] = (
            view
            if view in ("BULLISH", "BEARISH", "SIDEWAYS", "UNCERTAIN")
            else "UNCERTAIN"
        )
        scenarios = output.get("scenarios") or {}
        output["scenarios"] = {
            key: (
                scenarios.get(key)
                if isinstance(scenarios, dict) and isinstance(scenarios.get(key), str)
                else "Not provided by the model."
            )
            for key in ("bullish", "bearish", "sideways")
        }
        try:
            confidence = float(output.get("confidence", 0))
            output["confidence"] = (
                round(max(0, min(100, confidence))) if math.isfinite(confidence) else 0
            )
        except (ValueError, TypeError):
            output["confidence"] = 0
        output["confidence_level"] = (
            "HIGH"
            if output["confidence"] >= 70
            else "MEDIUM" if output["confidence"] >= 45 else "LOW"
        )
        for key in ("price", "target", "stop_loss"):
            try:
                value = float(output.get(key))
                output[key] = value if math.isfinite(value) and value > 0 else None
            except (TypeError, ValueError):
                output[key] = None
        if not isinstance(output.get("key_levels"), dict):
            output["key_levels"] = {}
        options = context.get("options") or {}
        output["option_comparison"] = (
            {
                "stronger_side": None,
                "call_delta": (options.get("atm_call") or {}).get("delta"),
                "put_delta": (options.get("atm_put") or {}).get("delta"),
                "call_itm_probability_pct": None,
                "put_itm_probability_pct": None,
                "basis": "Supplied option delta sensitivity. Not calibrated odds of profit or expiring ITM.",
            }
            if options
            else None
        )
        # Enforce the named daily statistical range, never a model-created target band.
        stats = context.get("historical_stats") or {}
        ranges = stats.get("range") or {}
        try:
            opening = float(quote["open"])
            lower = opening - float(ranges["downside_from_open_points"]["median"])
            upper = opening + float(ranges["upside_from_open_points"]["median"])
            valid = (
                all(math.isfinite(v) and v > 0 for v in (lower, upper))
                and lower <= upper
            )
        except (KeyError, TypeError, ValueError):
            lower = upper = None
            valid = False
        expectation = output.get("price_expectation")
        expectation = expectation if isinstance(expectation, dict) else {}
        indicators = context.get("indicators") or {}
        spot = quote.get("ltp")

        def verified_levels(keys, relation):
            result = []
            for key in keys:
                item = indicators.get(key)
                candidates = item.values() if isinstance(item, dict) else [item]
                for candidate in candidates:
                    try:
                        value = float(candidate)
                        if (
                            math.isfinite(value)
                            and value > 0
                            and spot is not None
                            and relation(value, float(spot))
                        ):
                            result.append(value)
                    except (ValueError, TypeError):
                        continue
            return result

        supports = verified_levels(
            ("CPR", "PIVOT"), lambda value, price: value <= price
        )
        resistances = verified_levels(
            ("CPR", "PIVOT"), lambda value, price: value >= price
        )
        output["price_expectation"] = {
            **expectation,
            "nearest_support": max(supports) if supports else None,
            "nearest_resistance": min(resistances) if resistances else None,
            "expected_range_low": round(lower, 2) if valid else None,
            "expected_range_high": round(upper, 2) if valid else None,
            "basis": (
                "Support/resistance use supplied CPR and pivot levels. Range uses daily median historical excursions from the most recent reference-session open; not a next-session forecast or confidence interval."
                if analysis_mode == "NEXT_SESSION" and valid
                else (
                    "Support/resistance use supplied CPR and pivot levels. Range uses daily median historical excursions from today's open; not a confidence interval or horizon-specific forecast."
                    if valid
                    else "Support/resistance use supplied CPR and pivot levels. Daily historical excursion range unavailable: verified history or reference-session open is missing."
                )
            ),
        }

    @staticmethod
    def _enforce_historical_probability(
        parsed: dict, market_context: dict
    ) -> Optional[str]:
        """Replace model-estimated percentages with Athena's measured baseline."""
        probability = parsed.get("probability")
        if not isinstance(probability, dict):
            probability = {}
        base = (market_context or {}).get("intraday_probability_base_rate")
        keys = ("upside_pct", "downside_pct", "sideways_pct")
        if not base:
            unavailable_reason = (market_context or {}).get(
                "intraday_probability_unavailable_reason",
                "Unavailable — insufficient horizon-matched completed-session history.",
            )
            parsed["probability"] = {
                **probability,
                **{key: None for key in keys},
                "basis": unavailable_reason,
            }
            return None

        expected = {key: base[key] for key in keys}
        mismatch = False
        for key in keys:
            value = probability.get(key)
            if value is None:
                continue
            try:
                mismatch = mismatch or abs(float(value) - float(expected[key])) > 0.11
            except (TypeError, ValueError):
                mismatch = True
        parsed["probability"] = {
            **probability,
            **expected,
            "basis": (
                f"Completed one-minute candle outcomes over {base['horizon_minutes']} minutes "
                f"(analysis interval {base['timeframe']}); "
                f"n={base['sample_size']}, "
                f"anchor {base['reference_minute_ist'] // 60:02d}:{base['reference_minute_ist'] % 60:02d} IST ±{base['time_of_day_tolerance_minutes']}m"
                if base.get("reference_minute_ist") is not None
                else f"Completed one-minute candle outcomes over {base['horizon_minutes']} minutes "
                f"(analysis interval {base['timeframe']}); n={base['sample_size']}, time-of-day ±{base['time_of_day_tolerance_minutes']}m"
            )
            + (
                f", sideways band ±{base['sideways_band_pct']}%, data through {base.get('latest_sample_date', 'unknown')}"
                f"; source: {base.get('source', 'stored candles')}."
            ),
            "sample_size": base["sample_size"],
            "low_confidence": base["low_confidence"],
        }
        if mismatch:
            return "AI probability was replaced with Athena's unchanged horizon-matched historical base rate."
        return None

    # ------------------------------------------------------------------
    # Risks list — strip anything referencing data that wasn't actually
    # supplied for this specific call
    # ------------------------------------------------------------------

    @classmethod
    def _clean_risks(cls, risks: list, market_context: dict) -> tuple[list, list[str]]:
        warnings = []
        cleaned = []
        for risk in risks:
            term = cls._find_ungrounded_term(str(risk), market_context)
            if term:
                warnings.append(
                    f"Stripped fabricated risk factor '{risk}' — "
                    f"{cls.REASONS[term]}"
                )
            else:
                cleaned.append(risk)
        return cleaned, warnings

    @classmethod
    def _find_ungrounded_term(cls, text: str, market_context: dict) -> Optional[str]:
        text_lower = text.lower()
        for term, is_grounded in cls.CONDITIONAL_TERMS.items():
            if term in text_lower and not is_grounded(market_context):
                return term
        return None

    # ------------------------------------------------------------------
    # Session claim — the model must report the session exactly as given
    # ------------------------------------------------------------------

    @staticmethod
    def _check_session_claim(market_context: dict, raw_content: str) -> Optional[str]:
        if not market_context or not raw_content:
            return None

        session_ctx = market_context.get("session") or {}
        actual_session = session_ctx.get("session")
        if not actual_session:
            return None

        match = re.search(r"\*\*Session:\*\*\s*([A-Z_]+)", raw_content)
        if not match:
            return None

        claimed_session = match.group(1)
        if claimed_session != actual_session:
            return (
                f"AI response claimed Session: {claimed_session} but the "
                f"actual session provided was {actual_session} — the model "
                f"did not report the given value accurately. This is a "
                f"prompt-adherence failure, not a missing-data issue."
            )
        return None
