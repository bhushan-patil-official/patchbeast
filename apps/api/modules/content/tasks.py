import httpx
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from modules.platform.services import post_indexnow
from modules.platform.task_base import AlertingTask

from . import selectors, stories


@shared_task(name="llm.build_stories", base=AlertingTask, time_limit=600, soft_time_limit=540)
def build_stories() -> int:
    """Beat (every 6 h): cluster similar articles and draft briefings for human review."""
    return stories.build_all()


@shared_task(
    name="publish.indexnow",
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=30,
    max_retries=3,
    time_limit=30,
    soft_time_limit=25,
)
def submit_indexnow(paths: list[str]) -> int:
    """Submit changed pages that are really in the sitemap (indexable), at most once per 10 minutes each."""
    indexable = {e["path"] for e in selectors.sitemap_entries()}
    fresh = [
        f"{settings.SITE_URL}{p}"
        for p in paths
        if p in indexable and cache.add(f"indexnow:{p}", 1, 600)
    ]
    return len(fresh) if post_indexnow(fresh) else 0
