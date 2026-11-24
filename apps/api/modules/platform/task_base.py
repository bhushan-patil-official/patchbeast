from celery import Task

from .services import raise_alert


class AlertingTask(Task):
    """Dead-letter handling: after retries are exhausted the failure is logged and alerted (rate-limited)."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        raise_alert("task_failed", f"{self.name} failed permanently: {exc.__class__.__name__}: {exc}", dedupe_key=f"task-{self.name}")
