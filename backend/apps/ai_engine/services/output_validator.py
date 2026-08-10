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
import re
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
        cleaned = dict(parsed) if parsed else {}

        cleaned["risks"], risk_warnings = cls._clean_risks(
            cleaned.get("risks") or [], market_context
        )
        warnings.extend(risk_warnings)

        session_warning = cls._check_session_claim(market_context, raw_content)
        if session_warning:
            warnings.append(session_warning)

        return {"parsed": cleaned, "warnings": warnings}

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