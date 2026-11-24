from celery import shared_task

from modules.platform.task_base import AlertingTask

from . import stories


@shared_task(name="llm.build_stories", base=AlertingTask, time_limit=600, soft_time_limit=540)
def build_stories() -> int:
    """Beat (every 6 h): cluster similar articles and draft briefings for human review."""
    return stories.build_all()
