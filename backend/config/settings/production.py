from django.core.exceptions import ImproperlyConfigured

from .base import *
import os

DEBUG = False

# SECRET_KEY signs every JWT and derives the key that encrypts stored AI
# provider credentials. base.py falls back to "change-me" for local
# convenience; running production with it would let anyone forge a login.
if SECRET_KEY == "change-me" or len(SECRET_KEY) < 32:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a unique value of at least 32 "
        "characters in production."
    )

# Production is the one place allowed to flip these on by default; an
# explicit LIVE_TRADING_ENABLED=True in the environment can also do so
# from any settings module — see base.py.
MARKET_PROVIDER = "zerodha"
LIVE_TRADING_ENABLED = True

# Production password reset links require a real email service. Configure its
# host and credentials through environment variables; never fall back to the
# development console backend in production.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
