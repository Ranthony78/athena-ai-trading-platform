import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# SECRET_KEY signs every JWT and derives the key that encrypts stored AI
# provider credentials. base.py falls back to "change-me" for local
# convenience; running production with it would let anyone forge a login.
if SECRET_KEY == "change-me" or len(SECRET_KEY) < 32:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a unique value of at least 32 "
        "characters in production."
    )

# Production starts with no cross-origin access: the local dev origins that
# base.py allows by default must not carry over. List the real frontend origin
# in CORS_ALLOWED_ORIGINS if it is served from a different origin than the API.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Production uses live Zerodha market data by default.
MARKET_PROVIDER = "zerodha"

# Real broker orders are OFF unless the server's environment turns them on:
# LIVE_TRADING_ENABLED is inherited from base.py, which reads the environment
# variable of the same name and treats anything other than exactly "True" as
# off. Nothing here forces it on, so a fresh or misconfigured deployment can
# never place a real order by accident.

# Production password reset links require a real email service. Configure its
# host and credentials through environment variables; never fall back to the
# development console backend in production.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
