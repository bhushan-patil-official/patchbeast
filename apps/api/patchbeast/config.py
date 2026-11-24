"""Typed environment configuration (pydantic-settings). Single source of truth for env vars."""

from functools import lru_cache
from urllib.parse import unquote, urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", case_sensitive=False)

    django_secret_key: str = "dev-insecure-change-me"
    django_allowed_hosts: str = "localhost,127.0.0.1,api"
    django_csrf_trusted_origins: str = ""
    site_url: str = "http://localhost:3000"
    database_url: str = "postgres://patchbeast:patchbeast@localhost:5432/patchbeast"
    redis_url: str = "redis://localhost:6379/0"

    revalidate_url: str = "http://web:3000/internal/revalidate"
    revalidate_secret: str = "dev-revalidate-secret"

    anthropic_api_key: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-haiku-5-5"
    llm_price_in_per_mtok: float = 0.10
    llm_price_out_per_mtok: float = 0.50
    llm_daily_cap_usd: float = 1.00
    auto_publish_threshold: float = 0.85

    youtube_api_key: str = ""
    youtube_daily_quota: int = 10000
    youtube_quota_safety_margin: int = 500
    websub_callback_base: str = ""

    email_host: str = "localhost"
    email_port: int = 1025
    email_host_user: str = ""
    email_host_password: str = ""
    email_use_tls: bool = False
    email_use_ssl: bool = False
    default_from_email: str = "Patchbeast <hello@patchbeast.com>"
    contact_email: str = "hello@patchbeast.com"

    alert_email_to: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    alert_cooldown_minutes: int = 60
    alert_5xx_rate_threshold: int = 10

    sentry_dsn: str = ""
    metrics_token: str = ""
    log_level: str = "INFO"

    feature_ads: bool = False
    feature_affiliate: bool = False
    feature_newsletter: bool = True
    feature_stories: bool = True
    story_max_per_day: int = 5
    story_similarity: float = 0.30
    story_window_days: int = 7
    feature_tier2_cheats: bool = False
    feature_tier2_maps: bool = False
    feature_tier3_alerts: bool = False

    cors_allowed_origins: str = Field(default="http://localhost:3000")

    def csv(self, value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]


@lru_cache
def get_env() -> Env:
    return Env()


def parse_database_url(url: str) -> dict:
    u = urlparse(url)
    if u.scheme in ("postgres", "postgresql"):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": u.path.lstrip("/"),
            "USER": unquote(u.username or ""),
            "PASSWORD": unquote(u.password or ""),
            "HOST": u.hostname or "",
            "PORT": str(u.port or 5432),
            "CONN_MAX_AGE": 60,
        }
    if u.scheme == "sqlite":
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": u.path or ":memory:"}
    raise ValueError(f"Unsupported DATABASE_URL scheme: {u.scheme}")
