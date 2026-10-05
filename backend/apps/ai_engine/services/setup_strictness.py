"""
Per-user "setup strictness": how readily the AI may return BUY/SELL instead of
NO_SETUP. It only changes the instructions given to the model. Every code-level
safety rule (stale or missing quotes, closed market, 14:00 IST cut-off,
NEXT_SESSION is planning only) and the measured historical probabilities are
enforced afterwards by the output validator and cannot be loosened here.
"""

STRICT = "STRICT"
BALANCED = "BALANCED"
EXPLORATORY = "EXPLORATORY"
LEVELS = (STRICT, BALANCED, EXPLORATORY)
DEFAULT_LEVEL = BALANCED

LABELS = {
    STRICT: "Strict",
    BALANCED: "Balanced",
    EXPLORATORY: "Exploratory",
}

_POLICY = {
    # Strict is the original behaviour: nothing is added to the prompt.
    STRICT: "",
    BALANCED: (
        "SETUP STRICTNESS: BALANCED (a user setting; it replaces the earlier line "
        "that NO_SETUP is the default). When valid, fresh evidence points mostly "
        "one way (trend, structure, indicators and option flow largely agree and "
        "the conflicting evidence is minor), you may return BUY or SELL as a LOW "
        "or MEDIUM confidence analytical candidate, and you must list the "
        "conflicting evidence and what is missing. Return NO_SETUP when the "
        "evidence is mixed, data is stale or missing, or any other rule blocks a "
        "current entry. Never raise confidence or any probability to justify a setup."
    ),
    EXPLORATORY: (
        "SETUP STRICTNESS: EXPLORATORY (a user setting for paper forward testing; "
        "it replaces the earlier line that NO_SETUP is the default). Whenever the "
        "supplied data is valid and fresh and market_view is not UNCERTAIN, return "
        "your best directional BUY or SELL candidate with confidence LOW unless the "
        "evidence is strong, state plainly that it is an exploratory candidate for "
        "paper testing and not a recommendation, and list the conflicting evidence. "
        "Return NO_SETUP only when data, session or timing rules block a current "
        "entry or the evidence is exactly balanced. Never raise confidence or any "
        "probability to justify a setup."
    ),
}


def normalize(level):
    value = str(level or "").upper()
    return value if value in LEVELS else DEFAULT_LEVEL


def get_level(user) -> str:
    """The user's saved level; Balanced when none is saved or lookup fails."""
    if user is None:
        return DEFAULT_LEVEL
    try:
        from ..models import AnalysisPreference

        row = AnalysisPreference.objects.filter(user=user).first()
        return normalize(row.setup_strictness) if row else DEFAULT_LEVEL
    except Exception:
        return DEFAULT_LEVEL


def policy_text(level) -> str:
    return _POLICY[normalize(level)]
