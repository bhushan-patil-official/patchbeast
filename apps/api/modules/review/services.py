"""Review actions (approve / reject / edit). Thin orchestration over content services + audit trail."""

from modules.content import services as content
from modules.content.models import Article, Video

from .models import ReviewAction


def _log(article: Article, action: str, user, note: str = "") -> None:
    ReviewAction.objects.create(
        article=article, action=action, note=note[:300], created_by=user, updated_by=user
    )


def parse_tags(raw: str) -> list[str]:
    return [t.strip().lower() for t in raw.replace(";", ",").split(",") if t.strip()][:6]


def approve(article_id: int, user, *, title=None, summary=None, tags: str | None = None) -> Article:
    a = Article.objects.select_related("game").get(pk=article_id)
    out = content.approve_article(
        a, user, title=title, summary=summary, tags=parse_tags(tags) if tags is not None else None
    )
    _log(a, ReviewAction.Action.APPROVE, user)
    return out


def reject(article_id: int, user, reason: str = "") -> Article:
    a = Article.objects.select_related("game").get(pk=article_id)
    out = content.reject_article(a, user, reason or "rejected in review")
    _log(a, ReviewAction.Action.REJECT, user, reason)
    return out


def save_edit(article_id: int, user, *, title: str, summary: str, tags: str) -> Article:
    a = Article.objects.get(pk=article_id)
    a.title, a.our_summary, a.tags, a.updated_by = title[:300], summary, parse_tags(tags), user
    a.save()
    _log(a, ReviewAction.Action.EDIT, user)
    return a


def video_decision(video_id: int, user, approve_it: bool) -> None:
    v = Video.objects.select_related("game").get(pk=video_id)
    if approve_it:
        content.approve_video(v, user)
    else:
        v.status = Video.Status.REJECTED
        v.updated_by = user
        v.save()


def queue(limit: int = 50):
    return (
        Article.objects.filter(status=Article.Status.QUEUED)
        .select_related("game", "source")
        .order_by("-confidence", "created_at")[:limit]
    )


def video_queue(limit: int = 20):
    return (
        Video.objects.filter(status=Video.Status.QUEUED)
        .select_related("game")
        .order_by("-published_at")[:limit]
    )
