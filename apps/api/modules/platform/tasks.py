import logging

import httpx
from celery import shared_task

from . import services

log = logging.getLogger(__name__)


@shared_task(
    name="publish.revalidate",
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=5,
    retry_backoff_max=300,
    max_retries=5,
    retry_jitter=True,
    acks_late=True,
    time_limit=30,
    soft_time_limit=25,
)
def revalidate(tags: list[str], paths: list[str]) -> None:
    try:
        services.post_revalidation(tags, paths)
    except httpx.HTTPError:
        from celery import current_task

        if current_task and current_task.request.retries >= 5:
            services.raise_alert(
                "revalidate_failed",
                f"ISR revalidation failed for tags={tags} paths={paths}",
                dedupe_key="revalidate",
            )
        raise


@shared_task(name="platform.check_alerts", time_limit=60)
def check_alerts() -> None:
    """Beat: 5xx rate, spend nearing cap, failing sources, review backlog."""
    from django.conf import settings

    n = services.current_5xx()
    if n >= settings.PB["ALERT_5XX_THRESHOLD"]:
        services.raise_alert(
            "5xx_rate", f"{n} server errors in the last 5 minutes", dedupe_key="5xx"
        )
    spent, cap = services.spend_today()
    if cap and spent >= cap * 9 / 10:
        services.raise_alert(
            "llm_spend_90",
            f"LLM spend ${spent:.4f} is >= 90% of daily cap ${cap}",
            dedupe_key=f"spend90-{spent//1}",
        )


@shared_task(name="platform.prune", time_limit=120)
def prune() -> None:
    services.prune_old()
