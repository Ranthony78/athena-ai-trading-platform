import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from config.database import database_config

# -----------------------------------------------------
# Paths
# -----------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR.parent / ".env")

# -----------------------------------------------------
# Core
# -----------------------------------------------------

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
]

# -----------------------------------------------------
# Django Apps
# -----------------------------------------------------

DJANGO_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# -----------------------------------------------------
# Third Party Apps
# -----------------------------------------------------

THIRD_PARTY_APPS = [
    "channels",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
]

# -----------------------------------------------------
# Local Apps
# -----------------------------------------------------

LOCAL_APPS = [
    "apps.accounts.apps.AccountsConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.market_data.apps.MarketDataConfig",
    "apps.ai_engine.apps.AiEngineConfig",
    "apps.paper_trading.apps.PaperTradingConfig",
    "apps.backtesting.apps.BacktestingConfig",
    "apps.journal.apps.JournalConfig",
    "apps.knowledge.apps.KnowledgeConfig",
    "apps.strategies.apps.StrategiesConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.zerodha.apps.ZerodhaConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# -----------------------------------------------------
# Middleware
# -----------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------------------------------------
# URLs
# -----------------------------------------------------

ROOT_URLCONF = "config.urls"

# -----------------------------------------------------
# Templates
# -----------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -----------------------------------------------------
# WSGI / ASGI
# -----------------------------------------------------

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# -----------------------------------------------------
# Database
# -----------------------------------------------------

# SQLite by default; PostgreSQL when DATABASE_URL or DB_ENGINE=postgres is set
# (see config/database.py).
DATABASES = {"default": database_config(os.environ, BASE_DIR)}

# -----------------------------------------------------
# Authentication
# -----------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

# -----------------------------------------------------
# Django REST Framework
# -----------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "shared.pagination.AthenaPagination",
    "PAGE_SIZE": 20,
    # Only views that opt in with throttle_scope are throttled (see
    # apps/accounts/views.py). Counters live in Django's cache, which is
    # per-process by default, so with N workers the effective limit is up to
    # N x the rate; point CACHES at Redis if that matters.
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",  # login, Google sign-in, password-reset confirm
        "register": "10/hour",  # account creation
        "refresh": "60/min",  # token refresh
    },
}

# -----------------------------------------------------
# Account registration
# -----------------------------------------------------

# Who may create an account:
#   "approval" - anyone may sign up, but the account stays inactive until a
#                staff member approves it in User Management (default).
#   "open"     - anyone may sign up and is signed in immediately.
#   "closed"   - nobody may sign up; staff create accounts (admin or
#                createsuperuser). Existing users, including those who use
#                Google sign-in, can still sign in.
# The same rule applies to first-time Google sign-in.
REGISTRATION_MODE = os.getenv("REGISTRATION_MODE", "approval").strip().lower()
if REGISTRATION_MODE not in {"approval", "open", "closed"}:
    raise ImproperlyConfigured(
        f"REGISTRATION_MODE must be 'approval', 'open' or 'closed' "
        f"(got {REGISTRATION_MODE!r})."
    )

# -----------------------------------------------------
# JWT
# -----------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# -----------------------------------------------------
# Swagger
# -----------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "Athena AI Trading Platform API",
    "DESCRIPTION": "REST API for Athena AI Trading Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [
        {
            "Bearer": [],
        }
    ],
    "SECURITY_SCHEMES": {
        "Bearer": {
            "TYPE": "http",
            "SCHEME": "bearer",
            "BEARER_FORMAT": "JWT",
        }
    },
}

# -----------------------------------------------------
# CORS
# -----------------------------------------------------

# Only these origins may call the API from a browser. The frontend sends its
# JWT in the Authorization header and never relies on cross-origin cookies, so
# credentialed CORS is switched off. In development the Vite proxy makes API
# calls same-origin anyway; the defaults below just allow the dev server.
# Set CORS_ALLOWED_ORIGINS (comma-separated, with scheme, e.g.
# https://app.example.com) for any other frontend origin.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = False

# -----------------------------------------------------
# Password Validation
# -----------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# -----------------------------------------------------
# Internationalization
# -----------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

# -----------------------------------------------------
# Static Files
# -----------------------------------------------------

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# -----------------------------------------------------
# Media Files
# -----------------------------------------------------

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------------------------------
# Default Primary Key
# -----------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------
# Market Provider
# -----------------------------------------------------

# Defaults to "mock" so an unconfigured environment never talks to the broker.
# Set MARKET_PROVIDER=zerodha in the environment (production.py does so
# explicitly) to use live market data.
MARKET_PROVIDER = os.getenv("MARKET_PROVIDER", "mock").strip().lower()

# Live broker order placement is a separate server-side gate from
# MARKET_PROVIDER. The shared default fails closed; environment-specific
# settings may explicitly enable it. ZerodhaOrderListAPIView enforces this
# gate independently of the selected market-data provider.
LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "False") == "True"

# Hard kill switch. When "True", real orders are refused whatever the
# in-app master switch or any user's arming says. It can only be set from
# the server environment, so it is the way to shut live trading off for
# everyone at once.
LIVE_TRADING_LOCKED = os.getenv("LIVE_TRADING_LOCKED", "False") == "True"

# -----------------------------------------------------
# Django Channels
# -----------------------------------------------------

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379")],
        },
    },
}


# -----------------------------------------------------
# AI Engine
# -----------------------------------------------------

AI_PROVIDER = (
    os.getenv("AI_PROVIDER", "gemini").strip().lower()
)  # mock | claude | gemini | groq

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", os.getenv("MOONSHOT_API_KEY", ""))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY", "")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k3").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()

# -----------------------------------------------------
# Celery — using filesystem broker for now (no Redis/Docker
# installed yet). Swap CELERY_BROKER_URL to redis://localhost:6379/0
# once Docker is set up — everything else here stays the same.
# -----------------------------------------------------
CELERY_BROKER_URL = "filesystem://"
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "data_folder_in": str(BASE_DIR / "broker" / "queue"),
    "data_folder_out": str(BASE_DIR / "broker" / "queue"),
    "data_folder_processed": str(BASE_DIR / "broker" / "processed"),
}
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_ENABLE_UTC = True


from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "track-signal-outcomes": {
        "task": "apps.market_data.tasks.track_signal_outcomes",
        "schedule": 60.0,  # paper exits and forecast sampling need minute-level cadence
    },
    "sync-intraday-candles": {
        "task": "apps.market_data.tasks.sync_intraday_candles",
        "schedule": 300.0,  # every 5 minutes — matches outcome tracking cadence
    },
    "snapshot-option-chain": {
        "task": "apps.market_data.tasks.snapshot_option_chain",
        "schedule": 300.0,  # every 5 minutes during market hours
    },
    "evening-next-session-analysis": {
        "task": "apps.ai_engine.tasks.run_scheduled_next_session_analysis",
        # 16:30 IST Mon-Fri, after the close and after the day's candles are in.
        "schedule": crontab(hour=16, minute=30, day_of_week="mon-fri"),
    },
    "purge-option-snapshots": {
        "task": "apps.market_data.tasks.purge_option_snapshots",
        "schedule": 86400.0,  # daily
    },
}

# -----------------------------------------------------
# Notifications
# -----------------------------------------------------

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@athena.ai")
EMAIL_TIMEOUT = 10
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


# -----------------------------------------------------
# Zerodha
# -----------------------------------------------------

ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", "")
ZERODHA_MCP_URL = os.getenv(
    "ZERODHA_MCP_URL",
    "https://mcp.kite.trade/mcp",
)

# -----------------------------------------------------
# Option analytics
# -----------------------------------------------------

# "black_scholes" (default, fixed-rate spot model) or "black76" (forward
# implied by put-call parity). Anything else falls back to black_scholes.
OPTION_IV_MODEL = os.getenv("OPTION_IV_MODEL", "black_scholes")
