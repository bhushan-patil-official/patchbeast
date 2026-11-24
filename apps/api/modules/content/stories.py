"""Automated story drafting: cluster similar articles, write an original briefing, queue it for review.

Safeguards: feature flag + kill switch + spend cap (SpendGuard) + per-day/per-run caps. Inputs are our
own summaries and verified facts only. Output is a DRAFT: a person approves it before it is public.
"""

import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from llm.factory import get_llm_client
from llm.guard import SpendGuard
from llm.ports import LLMError, LLMUnavailable
from llm.writer import StoryFailed, StoryInput, write_story
from modules.common.urlutils import registrable_domain
from modules.games.models import Game
from modules.platform import services as platform
from modules.platform.services import request_revalidation

from . import clustering
from .models import Article, Change, Story
from .services import compute_verification, game_tags, record_change

log = logging.getLogger(__name__)


def cluster_key(article_ids: list[int]) -> str:
    return hashlib.sha1(",".join(map(str, sorted(article_ids))).encode()).hexdigest()[
        :40
    ]  # noqa: S324


def candidate_articles(game: Game, days: int | None = None):
    """Articles that carry our own summary, are not rejected, and are not already in a live story."""
    since = timezone.now() - timedelta(days=days or settings.PB["STORY_WINDOW_DAYS"])
    used = Story.objects.exclude(status=Story.Status.REJECTED).values_list(
        "articles__id", flat=True
    )
    return (
        Article.objects.filter(game=game, created_at__gte=since, status__in=[Article.Status.QUEUED, Article.Status.PUBLISHED])
        .exclude(our_summary="")
        .exclude(id__in=[u for u in used if u])
        .select_related("game")
    )  # fmt: skip


def find_clusters(articles: list[Article]) -> list[list[Article]]:
    docs = [
        clustering.Doc(
            a.pk,
            f"{a.title} {a.our_summary}",
            registrable_domain(a.source_url),
            a.source_published_at or a.created_at,
        )
        for a in articles
    ]
    by_id = {a.pk: a for a in articles}
    groups = clustering.cluster(
        docs,
        threshold=settings.PB["STORY_SIMILARITY"],
        min_domains=settings.PB["STORY_MIN_SOURCES"],
    )
    return [[by_id[i] for i in g] for g in groups]


def _facts(game: Game, days: int) -> list[str]:
    since = timezone.now() - timedelta(days=days)
    qs = Change.objects.filter(game=game, is_public=True, occurred_at__gte=since).order_by(
        "-occurred_at"
    )[:8]
    return [
        f"{c.title}" + (f": {c.detail}" if c.detail else "") + f" ({c.verification})" for c in qs
    ]


def _unique_slug(game: Game, title: str) -> str:
    base = slugify(title)[:100] or "briefing"
    slug, n = base, 2
    while Story.objects.filter(game=game, slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def create_draft(game: Game, members: list[Article], client) -> Story | None:
    members = sorted(members, key=lambda a: (a.source_published_at or a.created_at))
    key = cluster_key([a.pk for a in members])
    if Story.objects.filter(game=game, cluster_key=key).exists():
        return None
    items = [
        StoryInput(i, a.title, a.our_summary, a.source_name or registrable_domain(a.source_url), (a.source_published_at or a.created_at).date().isoformat())
        for i, a in enumerate(members)
    ]  # fmt: skip
    facts = _facts(game, settings.PB["STORY_WINDOW_DAYS"])
    try:
        draft = write_story(client, game.name, items, facts)
    except StoryFailed as e:
        log.warning("story draft failed for %s: %s", key, e.reason)
        return None
    domains = {registrable_domain(a.source_url) for a in members}
    try:
        with transaction.atomic():
            story = Story.objects.create(
                game=game, slug=_unique_slug(game, draft.title), title=draft.title, dek=draft.dek,
                blocks=[b.model_dump() for b in draft.blocks], key_points=draft.key_points, tags=draft.tags,
                sources=[{"article_id": a.pk, "url": a.source_url, "name": items[i].source_name, "title": a.title} for i, a in enumerate(members)],
                cluster_key=key, verification=compute_verification(domains), model=getattr(client, "model", ""),
                review_reason=f"drafted from {len(members)} sources; check facts against the links",
            )  # fmt: skip
            story.articles.set(members)
    except IntegrityError:
        return None
    return story


def build_for_game(game: Game, client=None, *, max_new: int | None = None) -> list[Story]:
    if not platform.flag_enabled("stories") or platform.kill_switch_on():
        return []
    cap_day = settings.PB["STORY_MAX_PER_DAY"]
    today = Story.objects.filter(created_at__date=timezone.now().date()).count()
    budget = min(max_new or settings.PB["STORY_MAX_PER_RUN"], max(0, cap_day - today))
    if budget <= 0:
        return []
    llm = client or SpendGuard(get_llm_client(), purpose="story")
    made: list[Story] = []
    # biggest clusters first: the most-reported developments are the best briefing candidates
    for members in sorted(find_clusters(list(candidate_articles(game))), key=len, reverse=True):
        if len(made) >= budget:
            break
        try:
            story = create_draft(game, members, llm)
        except LLMUnavailable as e:
            log.info("story drafting paused: %s", e)
            break
        except LLMError as e:
            log.warning("story drafting LLM error: %s", e)
            continue
        if story:
            made.append(story)
    return made


def build_all(client=None) -> int:
    return sum(len(build_for_game(g, client)) for g in Game.objects.filter(enabled=True))


# ---------- review actions ----------
def approve_story(
    story: Story, user, *, title=None, dek=None, blocks: list[str] | None = None
) -> Story:
    if title is not None:
        story.title = title[:200]
    if dek is not None:
        story.dek = dek[:300]
    if blocks is not None:
        story.blocks = [
            {**b, "text": t.strip()}
            for b, t in zip(story.blocks, blocks, strict=False)
            if t.strip()
        ]
    if not story.blocks or not story.title.strip():
        raise ValueError("a story needs a title and at least one paragraph")
    story.status = Story.Status.PUBLISHED
    story.published_at = timezone.now()
    story.reviewed_at, story.reviewed_by, story.updated_by = timezone.now(), user, user
    story.save()
    record_change(
        story.game, Change.Kind.NEWS, f"Briefing: {story.title}", detail=story.dek,
        source_url=f"{settings.SITE_URL}/games/{story.game.slug}/news/{story.slug}",
        verification=story.verification, subject_kind="story", subject_id=story.pk,
    )  # fmt: skip
    request_revalidation(
        [*game_tags(story.game), "news", "stories"],
        ["/news", f"/games/{story.game.slug}/news", f"/games/{story.game.slug}/news/{story.slug}"],
    )
    return story


def reject_story(story: Story, user, reason: str = "") -> Story:
    was_published = story.status == Story.Status.PUBLISHED
    story.status = Story.Status.REJECTED
    story.review_reason = (reason or story.review_reason)[:300]
    story.reviewed_at, story.reviewed_by, story.updated_by = timezone.now(), user, user
    story.save()
    story.articles.clear()  # free the member articles so they can be re-clustered
    if was_published:
        Change.objects.filter(subject_kind="story", subject_id=story.pk).update(is_public=False)
        request_revalidation(
            [*game_tags(story.game), "news", "stories"], ["/news", f"/games/{story.game.slug}/news"]
        )
    return story
