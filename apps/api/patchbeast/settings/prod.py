from patchbeast.config import get_env

from .base import *

DEBUG = False
if SECRET_KEY.startswith("dev-insecure") and get_env().django_secret_key == SECRET_KEY:
    raise RuntimeError("Set DJANGO_SECRET_KEY for production")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # Caddy terminates TLS + redirects
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True

_env = get_env()
if _env.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=_env.sentry_dsn,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.0,
        send_default_pii=False,
    )
