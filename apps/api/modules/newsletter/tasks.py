from celery import shared_task
from django.db.models import F

from modules.platform.services import kill_switch_on
from modules.platform.task_base import AlertingTask

from . import services
from .models import DigestRun, Subscriber


@shared_task(name="mail.send_weekly_digest", base=AlertingTask, time_limit=120)
def send_weekly_digest() -> int:
    if kill_switch_on():
        return 0
    run, ids = services.start_weekly_digest()
    if run is None:
        return 0
    for sid in ids:
        send_digest_to_subscriber.delay(sid, run.iso_week)
    return len(ids)


@shared_task(
    name="mail.send_digest_to_subscriber",
    rate_limit="60/m",  # stay well inside email-provider rate limits; retries back off on errors
    base=AlertingTask,
    bind=True,
    max_retries=4,
    time_limit=60,
    acks_late=True,
)
def send_digest_to_subscriber(self, subscriber_id: int, week: str) -> bool:
    sub = Subscriber.objects.get(pk=subscriber_id)
    try:
        ok = services.send_digest_to(sub, week)
    except Exception as e:  # SMTP hiccup -> retry with backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries)) from e
    if ok:
        DigestRun.objects.filter(iso_week=week).update(sent=F("sent") + 1)
    return ok
