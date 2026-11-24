from .base import *

DEBUG = False
SECRET_KEY = "test"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
PB = {
    **PB,
    "LLM_PROVIDER": "fake",
    "ANTHROPIC_API_KEY": "",
    "AUTO_PUBLISH_THRESHOLD": 0.85,
    "LLM_DAILY_CAP_USD": 1.0,
    "ALERT_EMAIL_TO": "ops@example.com",
    "REVALIDATE_URL": "http://web.invalid/internal/revalidate",
    "YOUTUBE_API_KEY": "test-key",
}
LOGGING = {"version": 1, "disable_existing_loggers": False}
