"""Platform services: kill switch, spend cap, alerts, feature flags, revalidation, health."""

import logging
from collections.abc import Iterable
from datetime import timedelta
from decimal import Decimal

import httpx
from django.conf import settings
from django.core.cache import cache
from django.db import connection, transaction
from django.utils import timezone

from .models import AlertEvent, FeatureFlag, LLMUsage, SiteSetting
from .notifiers import get_notifiers

log = logging.getLogger(__name__)


# ---------- kill switch ----------
def kill_switch_on() -> bool:
    return SiteSetting.load().kill_switch


def set_kill_switch(on: bool, user=None) -> None:
    s = SiteSetting.load()
    s.kill_switch = on
    s.updated_by = user
    s.save()
    raise_alert(
        "kill_switch",
        f"Kill switch turned {'ON' if on else 'OFF'}",
        dedupe_key=f"ks-{on}-{timezone.now():%Y%m%d%H%M}",
    )


def auto_publish_allowed() -> bool:
    s = SiteSetting.load()
    return s.auto_publish_enabled and not s.kill_switch


# ---------- spend cap ----------
class SpendCapExceeded(Exception):
    pass


def _roll(s: SiteSetting) -> None:
    today = timezone.now().date()
    if s.spend_date != today:
        s.spend_date = today
        s.daily_llm_spend = Decimal("0")


def reserve_spend(estimate: Decimal) -> None:
    """Atomically reserve `estimate` USD against today's cap, or raise SpendCapExceeded."""
    SiteSetting.load()
    with transaction.atomic():
        s = SiteSetting.objects.select_for_update().get(pk=1)
        _roll(s)
        if s.daily_llm_spend + estimate > s.daily_llm_cap:
            s.save()
            breach = True
        else:
            s.daily_llm_spend += estimate
            s.save()
            breach = False
    if breach:
        raise_alert(
            "llm_spend_cap",
            f"Daily LLM cap ${s.daily_llm_cap} reached (spent ${s.daily_llm_spend:.4f}). Classification paused until tomorrow.",
            dedupe_key=f"spend-{timezone.now().date()}",
            cooldown_minutes=24 * 60,
        )
        raise SpendCapExceeded(f"daily cap {s.daily_llm_cap} reached")


def settle_spend(
    reserved: Decimal,
    actual: Decimal,
    *,
    model: str,
    tokens_in: int,
    tokens_out: int,
    purpose: str,
    ok: bool = True,
) -> None:
    with transaction.atomic():
        s = SiteSetting.objects.select_for_update().get(pk=1)
        _roll(s)
        s.daily_llm_spend = max(Decimal("0"), s.daily_llm_spend + (actual - reserved))
        s.save()
    LLMUsage.objects.create(
        day=timezone.now().date(), model=model, purpose=purpose, input_tokens=tokens_in,
        output_tokens=tokens_out, cost_usd=actual, ok=ok,
    )  # fmt: skip


def spend_today() -> tuple[Decimal, Decimal]:
    s = SiteSetting.load()
    if s.spend_date != timezone.now().date():
        return Decimal("0"), s.daily_llm_cap
    return s.daily_llm_spend, s.daily_llm_cap


# ---------- alerts ----------
def raise_alert(
    kind: str, message: str, *, dedupe_key: str | None = None, cooldown_minutes: int | None = None
) -> bool:
    """Send an alert through every configured Notifier unless the same key fired recently.
    Never raises (alerting must not break the caller)."""
    cooldown = (
        cooldown_minutes if cooldown_minutes is not None else settings.PB["ALERT_COOLDOWN_MINUTES"]
    )
    key = f"alert:{dedupe_key or kind}"
    if not cache.add(key, 1, timeout=cooldown * 60):
        return False
    delivered = []
    for n in get_notifiers():
        try:
            n.send(kind, message)
            delivered.append(n.name)
        except Exception:
            log.exception("notifier %s failed", n.name)
    try:
        AlertEvent.objects.create(
            kind=kind,
            message=message[:2000],
            dedupe_key=dedupe_key or "",
            delivered_via=",".join(delivered),
        )
    except Exception:
        log.exception("could not persist alert")
    return True


# ---------- feature flags ----------
def flag_enabled(key: str) -> bool:
    row = FeatureFlag.objects.filter(key=key).first()
    if row is not None:
        return row.enabled
    return bool(settings.PB["FLAG_DEFAULTS"].get(key, False))


def all_flags() -> dict[str, bool]:
    flags = dict(settings.PB["FLAG_DEFAULTS"])
    for row in FeatureFlag.objects.all():
        flags[row.key] = row.enabled
    return flags


# ---------- revalidation ----------
def request_revalidation(tags: Iterable[str] = (), paths: Iterable[str] = ()) -> None:
    """Schedule an ISR revalidation after the current transaction commits."""
    tags, paths = sorted(set(tags)), sorted(set(paths))
    if not tags and not paths:
        return
    from .tasks import revalidate

    transaction.on_commit(lambda: revalidate.delay(tags, paths))


def post_revalidation(
    tags: list[str], paths: list[str], client: httpx.Client | None = None
) -> None:
    c = client or httpx.Client(timeout=10)
    r = c.post(
        settings.PB["REVALIDATE_URL"],
        json={"tags": tags, "paths": paths},
        headers={"x-revalidate-secret": settings.PB["REVALIDATE_SECRET"]},
    )
    r.raise_for_status()


def post_indexnow(urls: list[str], client: httpx.Client | None = None) -> bool:
    """Tell IndexNow engines (Bing, Yandex, Seznam, Naver...) these URLs changed. No-op without a key
    or on localhost. Google does not use IndexNow: it relies on the sitemap + crawling."""
    from urllib.parse import urlparse

    key = settings.PB["INDEXNOW_KEY"]
    host = urlparse(settings.SITE_URL).hostname or ""
    if not key or not urls or host in ("", "localhost", "127.0.0.1"):
        return False
    c = client or httpx.Client(timeout=10)
    r = c.post(
        "https://api.indexnow.org/indexnow",
        json={
            "host": host,
            "key": key,
            "keyLocation": f"{settings.SITE_URL}/indexnow.txt",
            "urlList": urls[:100],
        },
    )
    r.raise_for_status()
    return True


# ---------- 5xx counter ----------
def _bucket() -> str:
    return f"5xx:{int(timezone.now().timestamp() // 300)}"


def count_5xx() -> None:
    k = _bucket()
    if not cache.add(k, 1, timeout=900):
        try:
            cache.incr(k)
        except ValueError:
            cache.set(k, 1, timeout=900)


def current_5xx() -> int:
    return int(cache.get(_bucket(), 0))


# ---------- health ----------
def health_checks() -> dict:
    out: dict = {}
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        out["db"] = "ok"
    except Exception as e:
        out["db"] = f"error: {e.__class__.__name__}"
    try:
        cache.set("healthz", "1", 10)
        out["cache"] = "ok" if cache.get("healthz") == "1" else "error"
    except Exception as e:
        out["cache"] = f"error: {e.__class__.__name__}"
    try:
        out["kill_switch"] = kill_switch_on()
    except Exception:
        out["kill_switch"] = None
    out["ok"] = out["db"] == "ok" and out["cache"] == "ok"
    return out


def prune_old(days: int = 60) -> None:
    cutoff = timezone.now() - timedelta(days=days)
    AlertEvent.objects.filter(created_at__lt=cutoff).delete()
    LLMUsage.objects.filter(created_at__lt=cutoff).delete()
