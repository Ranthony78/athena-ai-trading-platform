"""
Account-registration policy (see REGISTRATION_MODE in settings).

Both the password sign-up endpoint and first-time Google sign-in go through
this module, so the two paths can never disagree about who may get in.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

APPROVAL = "approval"
OPEN = "open"
CLOSED = "closed"

CLOSED_MESSAGE = (
    "Registration is closed. Ask an administrator to create an account for you."
)
PENDING_MESSAGE = (
    "Account created. An administrator must approve it before you can sign in."
)
INACTIVE_MESSAGE = (
    "This account is not active. If you just signed up, it is still waiting "
    "for administrator approval."
)


def registration_mode() -> str:
    """Return the configured mode; read on every call so tests can override it."""
    return getattr(settings, "REGISTRATION_MODE", APPROVAL)


def notify_staff_of_pending_user(user) -> None:
    """
    Tell active staff that an account is waiting for approval.

    Best effort only: a mail failure must never break sign-up, because the
    account is already saved and visible in User Management.
    """
    User = get_user_model()
    try:
        recipients = list(
            User.objects.filter(is_staff=True, is_active=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )
        if not recipients:
            return
        review_url = f"{settings.FRONTEND_URL.rstrip('/')}/admin/users"
        send_mail(
            subject="Athena: new account awaiting approval",
            message=(
                "A new account is waiting for approval.\n\n"
                f"Username: {user.username}\n"
                f"Email: {user.email}\n\n"
                f"Review it in User Management: {review_url}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception:  # never block sign-up on email trouble
        logger.warning("Could not notify staff about a pending account.", exc_info=True)
