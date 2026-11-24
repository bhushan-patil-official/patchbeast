import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_postrun, task_prerun

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "patchbeast.settings.dev")

app = Celery("patchbeast")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(
    [
        "modules.ingest",
        "modules.content",
        "modules.platform",
        "modules.newsletter",
        "modules.sources",
    ]
)

app.conf.beat_schedule = {
    "poll-due-sources": {"task": "ingest.poll_due_sources", "schedule": 60.0},
    "requeue-stuck-articles": {"task": "ingest.requeue_stuck", "schedule": 600.0},
    "check-health-alerts": {"task": "platform.check_alerts", "schedule": 300.0},
    "build-stories": {"task": "llm.build_stories", "schedule": crontab(minute=20, hour="*/6")},
    "renew-websub": {"task": "ingest.renew_websub", "schedule": crontab(hour=4, minute=10)},
    "prune-logs": {"task": "platform.prune", "schedule": crontab(hour=3, minute=40)},
    "weekly-digest": {
        "task": "mail.send_weekly_digest",
        "schedule": crontab(day_of_week="mon", hour=8, minute=0),
    },
}


@task_prerun.connect
def _bind_task_id(task_id=None, **_):
    from patchbeast.logging import task_id_var

    task_id_var.set(task_id or "-")


@task_postrun.connect
def _clear_task_id(**_):
    from patchbeast.logging import task_id_var

    task_id_var.set("-")
