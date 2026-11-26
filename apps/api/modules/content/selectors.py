"""Content reads + indexing policy. Indexable = real content only (never raw/placeholder)."""

from datetime import timedelta

from django.db.models import Max, QuerySet
from django.utils import timezone

from modules.common.choices import Verification
from modules.common.platforms import PLATFORMS, label
from modules.games.models import Game
from modules.games.selectors import current_releases, hub_path, release_history

from .models import Article, Change, Evidence, Patch, Requirement, Story, SubjectKind, Video


def real_releases(game: Game) -> list:
    return [
        r
        for r in current_releases(game)
        if not r.is_placeholder and r.date and r.confidence != Verification.RUMOUR
    ]


def real_requirements(game: Game) -> QuerySet:
    return Requirement.objects.filter(game=game, is_placeholder=False).exclude(cpu="", gpu="")


def real_patches(game: Game) -> QuerySet:
    return Patch.objects.filter(game=game, is_placeholder=False)


def published_videos(game: Game | None = None) -> QuerySet:
    qs = Video.objects.filter(status=Video.Status.PUBLISHED, is_placeholder=False)
    return qs.filter(game=game) if game else qs


def published_articles(game: Game | None = None) -> QuerySet:
    qs = Article.objects.filter(status=Article.Status.PUBLISHED).select_related("game")
    return qs.filter(game=game) if game else qs


def feed_articles() -> QuerySet:
    return (
        Article.objects.exclude(status=Article.Status.REJECTED)
        .select_related("game")
        .order_by("-created_at")
    )


def public_changes(
    game: Game | None = None, *, confirmed_only: bool = False, games: list[str] | None = None
) -> QuerySet:
    qs = Change.objects.filter(is_public=True, game__enabled=True).select_related("game")
    if game:
        qs = qs.filter(game=game)
    if games:
        qs = qs.filter(game__slug__in=games)
    if confirmed_only:
        qs = qs.filter(verification=Verification.CONFIRMED)
    return qs


def ticker_changes(limit: int = 10) -> QuerySet:
    return public_changes(confirmed_only=True)[:limit]


def weekly_changes(since=None, games: list[str] | None = None) -> QuerySet:
    since = since or timezone.now() - timedelta(days=7)
    return (
        public_changes(confirmed_only=True, games=games)
        .filter(occurred_at__gte=since)
        .order_by("game__name", "-occurred_at")
    )


def platform_options(game: Game) -> list[dict]:
    return [{"id": p, "name": label(p)} for p in game.platforms if p in PLATFORMS]


def seo_for_game(game: Game) -> dict:
    if not game.allow_index:
        return {"indexable": False, "reason": "disabled by editor"}
    has = bool(
        real_releases(game)
        or real_requirements(game).exists()
        or real_patches(game).exists()
        or published_videos(game).exists()
        or published_articles(game).exists()
    )
    return {"indexable": has, "reason": "" if has else "placeholder: no real content yet"}


def seo_subpage(game: Game, kind: str) -> dict:
    base = seo_for_game(game)
    if not base["indexable"]:
        return base
    exists = {
        "patches": real_patches(game).exists,
        "videos": published_videos(game).exists,
        "requirements": real_requirements(game).exists,
    }[kind]()
    return {"indexable": exists, "reason": "" if exists else f"no real {kind} yet"}


def latest_patches(limit: int = 6) -> list[Patch]:
    """Newest real, sourced patches across enabled games (for the home page and the RSS feed)."""
    out: list[Patch] = []
    qs = (
        Patch.objects.filter(is_placeholder=False, game__enabled=True)
        .select_related("game")
        .order_by("-date", "-created_at")
    )
    for p in qs[: limit * 4]:
        n = Evidence.objects.filter(subject_kind=SubjectKind.PATCH, subject_id=p.pk).count()
        if seo_for_patch(p.game, p, n)["indexable"]:
            out.append(p)
        if len(out) >= limit:
            break
    return out


def sitemap_entries() -> list[dict]:
    out: list[dict] = [{"path": "/", "lastmod": None}]
    news = published_articles()
    if news.exists():
        out.append({"path": "/news", "lastmod": news.aggregate(m=Max("published_at"))["m"]})
    for g in Game.objects.filter(enabled=True):
        if not seo_for_game(g)["indexable"]:
            continue
        last = public_changes(g).aggregate(m=Max("occurred_at"))["m"]
        out.append({"path": hub_path(g), "lastmod": last})
        for sub in ("patches", "videos", "requirements"):
            if seo_subpage(g, sub)["indexable"]:
                out.append({"path": f"/games/{g.slug}/{sub}", "lastmod": last})
        for st in published_stories(g):
            if seo_for_story(g, st)["indexable"]:
                out.append({"path": f"/games/{g.slug}/news/{st.slug}", "lastmod": st.updated_at})
        if published_articles(g).exists():
            newest = published_articles(g).aggregate(m=Max("published_at"))["m"]
            out.append({"path": f"/games/{g.slug}/news", "lastmod": newest})
        if has_public_changes(g):
            out.append({"path": f"/games/{g.slug}/timeline", "lastmod": last})
        for patch in real_patches(g):
            n = Evidence.objects.filter(subject_kind=SubjectKind.PATCH, subject_id=patch.pk).count()
            if seo_for_patch(g, patch, n)["indexable"]:
                out.append(
                    {
                        "path": f"/games/{g.slug}/patches/{patch.platform}/{patch.version}",
                        "lastmod": patch.updated_at,
                    }
                )
    newest = [e["lastmod"] for e in out if e["lastmod"]]
    out[0]["lastmod"] = max(newest) if newest else None
    return out


def hub_for_game(game: Game) -> dict:
    releases = current_releases(game)
    primary = next((r for r in releases if r.platform == game.platforms[0]), None)
    return {
        "release": primary,
        "releases": releases,
        "release_history": list(release_history(game)[:12]),
        "requirements": list(Requirement.objects.filter(game=game)),
        "patches": list(Patch.objects.filter(game=game)[:6]),
        "videos": list(published_videos(game)[:6]),
        "changes": list(public_changes(game)[:15]),
        "news": list(published_articles(game).order_by("-published_at")[:8]),
        "stories": list(published_stories(game)[:3]),
    }


def count_needs_review() -> int:
    return (
        Article.objects.filter(status=Article.Status.QUEUED).count()
        + Video.objects.filter(status=Video.Status.QUEUED).count()
    )


def patch_sources(patch: Patch) -> list[Evidence]:
    return list(
        Evidence.objects.filter(subject_kind=SubjectKind.PATCH, subject_id=patch.pk).order_by(
            "created_at"
        )
    )


def seo_for_patch(game: Game, patch: Patch, n_sources: int) -> dict:
    base = seo_for_game(game)
    if not base["indexable"]:
        return base
    real = (
        not patch.is_placeholder and n_sources >= 1 and bool(patch.our_summary or patch.highlights)
    )
    return {"indexable": real, "reason": "" if real else "patch page has no sourced content yet"}


def has_public_changes(game: Game) -> bool:
    return public_changes(game).exists()


def published_stories(game: Game | None = None) -> QuerySet:
    qs = Story.objects.filter(status=Story.Status.PUBLISHED, game__enabled=True).select_related(
        "game"
    )
    return (qs.filter(game=game) if game else qs).order_by("-published_at")


def seo_for_story(game: Game, story: Story) -> dict:
    base = seo_for_game(game)
    if not base["indexable"] and not base["reason"].startswith("placeholder"):
        return base  # editor disabled indexing
    ok = (
        story.status == Story.Status.PUBLISHED
        and len(story.sources) >= 2
        and bool(story.blocks)
        and game.allow_index
    )
    return {
        "indexable": ok,
        "reason": "" if ok else "story is not published or has fewer than two sources",
    }
