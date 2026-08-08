from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import os

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

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
}

# -----------------------------------------------------
# JWT
# -----------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
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

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

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

MARKET_PROVIDER = "zerodha" # mock

# -----------------------------------------------------
# Django Channels
# -----------------------------------------------------

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
            ],
        },
    },
}


# -----------------------------------------------------
# AI Engine
# -----------------------------------------------------

AI_PROVIDER = "kimi"  # mock | claude | groq | kimi

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

KIMI_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

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


CELERY_BEAT_SCHEDULE = {
    "track-signal-outcomes": {
        "task": "apps.market_data.tasks.track_signal_outcomes",
        "schedule": 300.0,  # every 5 minutes
    },
}

# -----------------------------------------------------
# Notifications
# -----------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@athena.ai"

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