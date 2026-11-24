"""Review actions (approve / reject / edit). Thin orchestration over content services + audit trail."""

from modules.content import services as content
from modules.content import stories as story_services
from modules.content.models import Article, Story, Video
from modules.games.models import Game

from .models import ReviewAction


def _log(article: Article, action: str, user, note: str = "") -> None:
    ReviewAction.objects.create(
        article=article, action=action, note=note[:300], created_by=user, updated_by=user
    )


def parse_tags(raw: str) -> list[str]:
    return [t.strip().lower() for t in raw.replace(";", ",").split(",") if t.strip()][:6]


def _apply_game(a: Article, game_slug: str | None, user) -> None:
    """Dropdown value: '' = leave as is, '<slug>' = attach/move to that game."""
    if not game_slug or (a.game and a.game.slug == game_slug):
        return
    g = Game.objects.filter(slug=game_slug).first()
    if g is None:
        raise ValueError(f"unknown game {game_slug!r}")
    content.assign_game(a, g, user)


def approve(
    article_id: int,
    user,
    *,
    title=None,
    summary=None,
    tags: str | None = None,
    game: str | None = None,
) -> Article:
    a = Article.objects.select_related("game").get(pk=article_id)
    _apply_game(a, game, user)
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


def save_edit(
    article_id: int, user, *, title: str, summary: str, tags: str, game: str | None = None
) -> Article:
    a = Article.objects.select_related("game").get(pk=article_id)
    _apply_game(a, game, user)
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


def queue(limit: int = 50, game: str | None = None):
    """Queued articles. game: a slug, 'unassigned', or None for all."""
    qs = Article.objects.filter(status=Article.Status.QUEUED).select_related("game", "source")
    if game == "unassigned":
        qs = qs.filter(game__isnull=True)
    elif game:
        qs = qs.filter(game__slug=game)
    return qs.order_by("game__name", "-confidence", "created_at")[:limit]


def queue_counts() -> dict[str, int]:
    """Queued articles per game slug ('unassigned' for none)."""
    from django.db.models import Count

    rows = (
        Article.objects.filter(status=Article.Status.QUEUED)
        .values("game__slug")
        .annotate(n=Count("id"))
    )
    return {(r["game__slug"] or "unassigned"): r["n"] for r in rows}


def bulk(action: str, ids: list[int], user, reason: str = "") -> list[str]:
    """Bulk curation. Returns human-readable result lines (never raises for one bad item)."""
    arts = list(
        Article.objects.filter(pk__in=ids, status=Article.Status.QUEUED).select_related("game")
    )
    out: list[str] = []
    if not arts:
        return ["nothing selected (or already handled)"]
    if action == "reject":
        for a in arts:
            content.reject_article(a, user, reason or "rejected in bulk review")
            _log(a, ReviewAction.Action.REJECT, user, reason)
        return [f"rejected {len(arts)} article(s)"]
    if action == "approve_linked":
        done = 0
        for a in arts:
            try:
                content.approve_article(a, user)
                _log(a, ReviewAction.Action.APPROVE, user)
                done += 1
            except ValueError as e:
                out.append(f"#{a.pk} skipped: {e}")
        return [f"approved {done} as linked news", *out]
    if action == "merge":
        try:
            story = story_services.merge_articles(arts)
        except ValueError as e:
            return [f"could not merge: {e}"]
        return [
            f"drafted one briefing from {len(arts)} articles: “{story.title}” (see Story drafts)"
        ]
    return [f"unknown action {action!r}"]


def video_queue(limit: int = 20):
    return (
        Video.objects.filter(status=Video.Status.QUEUED)
        .select_related("game")
        .order_by("-published_at")[:limit]
    )


def story_queue(limit: int = 20):
    return (
        Story.objects.filter(status=Story.Status.DRAFT)
        .select_related("game")
        .order_by("-created_at")[:limit]
    )


def story_decision(
    story_id: int,
    user,
    action: str,
    *,
    title=None,
    dek=None,
    blocks: list[str] | None = None,
    reason: str = "",
):
    st = Story.objects.select_related("game").get(pk=story_id)
    if action == "approve":
        return story_services.approve_story(st, user, title=title, dek=dek, blocks=blocks)
    if action == "reject":
        return story_services.reject_story(st, user, reason or "rejected in review")
    if action == "save":
        if title is not None:
            st.title = title[:200]
        if dek is not None:
            st.dek = dek[:300]
        if blocks is not None:
            st.blocks = [
                {**b, "text": t.strip()}
                for b, t in zip(st.blocks, blocks, strict=False)
                if t.strip()
            ]
        st.updated_by = user
        st.save()
        return st
    raise ValueError("unknown action")
