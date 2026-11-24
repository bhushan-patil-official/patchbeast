from pathlib import Path
from typing import Any

from patchbeast.config import get_env, parse_database_url
from patchbeast.logging import logging_config

env = get_env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env.django_secret_key
DEBUG = False
ALLOWED_HOSTS = env.csv(env.django_allowed_hosts)
CSRF_TRUSTED_ORIGINS = env.csv(env.django_csrf_trusted_origins)
SITE_URL = env.site_url.rstrip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "modules.platform",
    "modules.games",
    "modules.sources",
    "modules.ingest",
    "modules.content",
    "modules.review",
    "modules.newsletter",
]

MIDDLEWARE = [
    "patchbeast.logging.RequestIdMiddleware",
    "modules.platform.middleware.ServerErrorCounterMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "patchbeast.cors.SimpleCorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "patchbeast.urls"
WSGI_APPLICATION = "patchbeast.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {"default": parse_database_url(env.database_url)}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.redis_url,
        "KEY_PREFIX": "pb",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "modules.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "600/hour", "newsletter": "10/hour"},
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Patchbeast API",
    "DESCRIPTION": "Read API for the Patchbeast launch tracker. The OpenAPI schema is the contract.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "VerificationEnum": "modules.common.choices.Verification",
    },
}

CORS_ALLOWED_ORIGINS = env.csv(env.cors_allowed_origins)

# --- Celery ---
CELERY_BROKER_URL = env.redis_url
CELERY_RESULT_BACKEND = None
CELERY_TASK_DEFAULT_QUEUE = "celery"
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 60
CELERY_TASK_TIME_LIMIT = 90
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 3600}
CELERY_TASK_ROUTES = {
    "ingest.*": {"queue": "ingest"},
    "llm.*": {"queue": "llm"},
    "publish.*": {"queue": "publish"},
    "mail.*": {"queue": "mail"},
    "platform.*": {"queue": "ingest"},
}

# --- Email ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.email_host
EMAIL_PORT = env.email_port
EMAIL_HOST_USER = env.email_host_user
EMAIL_HOST_PASSWORD = env.email_host_password
EMAIL_USE_TLS = env.email_use_tls
DEFAULT_FROM_EMAIL = env.default_from_email
EMAIL_TIMEOUT = 10

# --- Patchbeast ---
PB: dict[str, Any] = {
    "LLM_PROVIDER": env.llm_provider,
    "LLM_MODEL": env.llm_model,
    "ANTHROPIC_API_KEY": env.anthropic_api_key,
    "LLM_PRICE_IN": env.llm_price_in_per_mtok,
    "LLM_PRICE_OUT": env.llm_price_out_per_mtok,
    "LLM_DAILY_CAP_USD": env.llm_daily_cap_usd,
    "AUTO_PUBLISH_THRESHOLD": env.auto_publish_threshold,
    "YOUTUBE_API_KEY": env.youtube_api_key,
    "YOUTUBE_DAILY_QUOTA": env.youtube_daily_quota,
    "YOUTUBE_SAFETY_MARGIN": env.youtube_quota_safety_margin,
    "WEBSUB_CALLBACK_BASE": env.websub_callback_base,
    "REVALIDATE_URL": env.revalidate_url,
    "REVALIDATE_SECRET": env.revalidate_secret,
    "ALERT_EMAIL_TO": env.alert_email_to,
    "TELEGRAM_BOT_TOKEN": env.telegram_bot_token,
    "TELEGRAM_CHAT_ID": env.telegram_chat_id,
    "ALERT_COOLDOWN_MINUTES": env.alert_cooldown_minutes,
    "ALERT_5XX_THRESHOLD": env.alert_5xx_rate_threshold,
    "METRICS_TOKEN": env.metrics_token,
    "CONTACT_EMAIL": env.contact_email,
    "FLAG_DEFAULTS": {
        "ads": env.feature_ads,
        "affiliate": env.feature_affiliate,
        "newsletter": env.feature_newsletter,
        "tier2_cheats": env.feature_tier2_cheats,
        "tier2_maps": env.feature_tier2_maps,
        "tier3_alerts": env.feature_tier3_alerts,
    },
    "USER_AGENT": "PatchbeastBot/1.0 (+https://patchbeast.com/about#bot)",
    "NEAR_DUP_HAMMING": 3,
    "SOURCE_MAX_BACKOFF_MINUTES": 360,
    "SOURCE_AUTO_DISABLE_DAYS": 7,
}

LOGGING = logging_config(env.log_level)
