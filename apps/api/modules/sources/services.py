"""Source registry writes: spec building, success/failure bookkeeping, backoff, due selection."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from modules.platform.services import raise_alert

from .models import Source
from .ports import FetchResult, SourceSpec


def to_spec(source: Source) -> SourceSpec:
    return SourceSpec(
        id=source.id, type=source.type, url=source.url, etag=source.etag, last_modified=source.last_modified,
        config=source.config or {}, official_feed=source.official_feed, name=source.name,
    )  # fmt: skip


def due_sources(now=None):
    now = now or timezone.now()
    return Source.objects.filter(
        enabled=True, is_placeholder=False, next_fetch_at__lte=now, game__enabled=True
    ).exclude(type=Source.Type.WEBSUB)


def mark_success(source: Source, result: FetchResult) -> None:
    now = timezone.now()
    source.last_fetched = now
    source.consecutive_failures = 0
    source.failing_since = None
    source.last_error = ""
    source.health = Source.Health.OK
    if result.etag:
        source.etag = result.etag
    if result.last_modified:
        source.last_modified = result.last_modified
    source.next_fetch_at = now + timedelta(minutes=max(5, min(15, source.interval_minutes)))
    source.save()


def backoff_minutes(failures: int, base: int = 10) -> int:
    return min(base * (2 ** max(0, failures - 1)), settings.PB["SOURCE_MAX_BACKOFF_MINUTES"])


def mark_failure(
    source: Source, message: str, *, retry_after: int | None = None, permanent: bool = False
) -> None:
    now = timezone.now()
    source.consecutive_failures += 1
    source.last_error = message[:500]
    source.failing_since = source.failing_since or now
    delay = backoff_minutes(source.consecutive_failures, max(5, source.interval_minutes))
    if retry_after:
        delay = max(delay, retry_after // 60 + 1)
    source.next_fetch_at = now + timedelta(minutes=delay)
    source.health = (
        Source.Health.FAILING
        if source.consecutive_failures >= 3 or permanent
        else Source.Health.DEGRADED
    )
    disable = permanent and source.consecutive_failures >= 2
    if now - source.failing_since > timedelta(days=settings.PB["SOURCE_AUTO_DISABLE_DAYS"]):
        disable = True
    if disable:
        source.enabled = False
    source.save()
    if source.health == Source.Health.FAILING:
        raise_alert(
            "fetcher_failure",
            f"Source '{source.name}' ({source.type}) failing x{source.consecutive_failures}: {message}"
            + (" — AUTO-DISABLED" if disable else ""),
            dedupe_key=f"fetch-{source.id}-{int(disable)}",
        )
