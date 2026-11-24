import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from llm.ports import LLMRetryable
from modules.platform.services import kill_switch_on
from modules.platform.task_base import AlertingTask

from . import services

log = logging.getLogger(__name__)


@shared_task(name="ingest.poll_due_sources", time_limit=60)
def poll_due_sources() -> int:
    from datetime import timedelta

    from modules.sources.services import due_sources

    if kill_switch_on():
        return 0
    n = 0
    for s in due_sources():
        s.next_fetch_at = timezone.now() + timedelta(minutes=2)  # claim: avoid double dispatch
        s.save(update_fields=["next_fetch_at"])
        fetch_source.delay(s.pk)
        n += 1
    return n


@shared_task(
    name="ingest.fetch_source", base=AlertingTask, time_limit=90, soft_time_limit=75, acks_late=True
)
def fetch_source(source_id: int) -> None:
    services.fetch_and_ingest(source_id)


@shared_task(
    name="llm.classify_article",
    base=AlertingTask,
    bind=True,
    max_retries=3,
    time_limit=120,
    soft_time_limit=100,
    acks_late=True,
)
def classify_article_task(self, article_id: int, lead: str) -> str:
    try:
        return services.classify_article(article_id, lead)
    except LLMRetryable as e:
        if self.request.retries >= self.max_retries:
            from modules.content import services as content
            from modules.content.models import Article

            a = Article.objects.get(pk=article_id)
            if a.status == Article.Status.NEW:
                content.queue_for_review(a, f"LLM unreachable after retries: {e}")
            return "queued-retries-exhausted"
        raise self.retry(exc=e, countdown=30 * (2**self.request.retries)) from e


@shared_task(name="ingest.requeue_stuck", time_limit=60)
def requeue_stuck() -> int:
    return services.requeue_stuck()


@shared_task(name="ingest.renew_websub", time_limit=120)
def renew_websub() -> int:
    from modules.sources.fetchers import websub
    from modules.sources.models import Source

    base = settings.PB["WEBSUB_CALLBACK_BASE"].rstrip("/")
    if not base or kill_switch_on():
        return 0
    n = 0
    for s in Source.objects.filter(type=Source.Type.WEBSUB, enabled=True, is_placeholder=False):
        try:
            websub.subscribe(
                s.config["channel_id"], f"{base}/hooks/websub/{s.pk}/", s.config.get("secret", "")
            )
            n += 1
        except Exception:
            log.exception("websub renew failed for %s", s.pk)
    return n
