"""
backend/apps/zerodha/exceptions.py

New file — place at: backend/apps/zerodha/exceptions.py

Distinguishes "token expired, user needs to reconnect" from other Zerodha
failures, so the API layer can return the right HTTP status and the frontend
can react correctly instead of every failure mode collapsing into the same
generic error dict.
"""


class ZerodhaError(Exception):
    """Base class for Zerodha-related errors."""


class ZerodhaTokenExpiredError(ZerodhaError):
    """
    Raised when Kite rejects a call because the daily access token has
    expired or is otherwise invalid. The caller should prompt the user to
    reconnect (GET /api/zerodha/login-url/) rather than treat this as a
    generic failure.
    """


def is_token_expiry_message(message: str) -> bool:
    """
    Kite's own error strings for this case aren't perfectly consistent, so
    this checks for the substrings actually seen in practice. Adjust/extend
    this list if you see a new phrasing show up in logs.
    """
    message_lower = message.lower()
    return any(
        phrase in message_lower
        for phrase in (
            "access token is invalid",
            "access token is expired",
            "token is invalid or expired",
            "invalid or expired",
        )
    )