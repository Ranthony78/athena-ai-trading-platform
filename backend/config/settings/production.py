from .base import *
import os

DEBUG = False

# Production is the one place allowed to flip these on by default; an
# explicit LIVE_TRADING_ENABLED=True in the environment can also do so
# from any settings module — see base.py.
MARKET_PROVIDER = "zerodha"
LIVE_TRADING_ENABLED = True

# Production password reset links require a real email service. Configure its
# host and credentials through environment variables; never fall back to the
# development console backend in production.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
