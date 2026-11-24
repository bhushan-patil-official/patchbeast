"""Content writes: evidence + verification, publish rules, approve/reject.

Verification model: Confirmed = 2 independent sources (distinct registrable domains) or a video;
Reported = one linked source; Rumour = none."""

from datetime import date as date_t
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from modules.common.choices import VERIFICATION_RANK, Verification
from modules.common.urlutils import registrable_domain
from modules.games import services as games_services
from modules.games.models import Game, Release
from modules.games.selectors import current_release
from modules.platform.services import auto_publish_allowed, request_revalidation

from .models import Article, Change, Evidence, Patch, Requirement, SubjectKind, Video

SUBJECT_MODELS = {
    SubjectKind.RELEASE: Release,
    SubjectKind.PATCH: Patch,
    SubjectKind.REQUIREMENT: Requirement,
    SubjectKind.ARTICLE: Article,
    SubjectKind.VIDEO: Video,
}


# ---------- verification ----------
def compute_verification(domains: set[str], has_video: bool = False) -> str:
    if has_video or len(domains) >= 2:
        return Verification.CONFIRMED
    if len(domains) == 1:
        return Verification.REPORTED
    return Verification.RUMOUR


def add_evidence(
    game: Game, subject_kind: str, subject_id: int, url: str, kind: str = Evidence.Kind.ARTICLE
) -> Evidence:
    domain = registrable_domain(url)
    ev, _ = Evidence.objects.get_or_create(
        subject_kind=subject_kind,
        subject_id=subject_id,
        domain=domain,
        defaults={"game": game, "url": url, "kind": kind},
    )
    return ev


def recompute_verification(subject_kind: str, subject_id: int) -> tuple[str, str]:
    """Recompute and store verification for a subject. Returns (old, new)."""
    ev = list(Evidence.objects.filter(subject_kind=subject_kind, subject_id=subject_id))
    new = compute_verification(
        {e.domain for e in ev}, any(e.kind == Evidence.Kind.VIDEO for e in ev)
    )
    model: Any = SUBJECT_MODELS[SubjectKind(subject_kind)]
    obj = model.objects.get(pk=subject_id)
    field = "confidence" if subject_kind == SubjectKind.RELEASE else "verification"
    old = getattr(obj, field)
    updates: dict[str, Any] = {field: new}
    if hasattr(obj, "source_count"):
        updates["source_count"] = len({e.domain for e in ev})
    model.objects.filter(pk=subject_id).update(**updates)
    return old, new


def game_tags(game: Game) -> list[str]:
    return [f"game:{game.slug}", "games", "ticker", "sitemap"]


def record_change(game: Game, kind: str, title: str, *, detail: str = "", version_label: str = "", source_url: str = "",
                  verification: str = Verification.REPORTED, subject_kind: str = "", subject_id: int | None = None,
                  occurred_at: datetime | None = None) -> Change:  # fmt: skip
    return Change.objects.create(
        game=game, kind=kind, title=title[:240], detail=detail[:500], version_label=version_label[:60], source_url=source_url,
        verification=verification, subject_kind=subject_kind, subject_id=subject_id, occurred_at=occurred_at or timezone.now(),
    )  # fmt: skip


# ---------- facts ----------
class FactDeferred(Exception):
    """Fact is valid but must go through human review (reason in str(e))."""


def _fmt_date(d: date_t | None) -> str:
    return d.isoformat() if d else "unknown"


@transaction.atomic
def publish_release_fact(
    game: Game, *, date_: date_t, source_url: str, platform: str = "pc"
) -> Release:
    cur = current_release(game, platform)
    if cur and cur.date == date_ and not cur.is_placeholder:
        add_evidence(game, SubjectKind.RELEASE, cur.pk, source_url)
        old, new = recompute_verification(SubjectKind.RELEASE, cur.pk)
        if old != new:
            record_change(game, Change.Kind.RELEASE, f"Release date now {new.capitalize()}", detail=f"{date_.isoformat()} ({old} -> {new})",
                          source_url=source_url, verification=new, subject_kind=SubjectKind.RELEASE, subject_id=cur.pk)  # fmt: skip
        return cur
    real_current = cur is not None and not cur.is_placeholder and cur.date is not None
    if (
        cur is not None
        and real_current
        and VERIFICATION_RANK[Verification.REPORTED] < VERIFICATION_RANK[cur.confidence]
    ):
        raise FactDeferred(f"conflicts with {cur.confidence} date {cur.date}; needs human review")
    new_rel, prev = games_services.set_current_release(game, date_=date_, confidence=Verification.REPORTED, source_url=source_url,
                                                       source_count=1, platform=platform)  # fmt: skip
    add_evidence(game, SubjectKind.RELEASE, new_rel.pk, source_url)
    recompute_verification(SubjectKind.RELEASE, new_rel.pk)
    new_rel.refresh_from_db()
    record_change(game, Change.Kind.RELEASE, "Release date updated", detail=f"{_fmt_date(prev.date if prev else None)} -> {date_.isoformat()}",
                  source_url=source_url, verification=new_rel.confidence, subject_kind=SubjectKind.RELEASE, subject_id=new_rel.pk)  # fmt: skip
    return new_rel


@transaction.atomic
def publish_patch_fact(
    game: Game, *, version: str, date_: date_t | None, source_url: str, summary: str
) -> Patch:
    patch, created = Patch.objects.get_or_create(
        game=game,
        version=version,
        defaults={
            "date": date_,
            "notes_url": source_url,
            "our_summary": summary,
            "source_count": 1,
        },
    )
    add_evidence(game, SubjectKind.PATCH, patch.pk, source_url)
    old, new = recompute_verification(SubjectKind.PATCH, patch.pk)
    if created or old != new:
        record_change(game, Change.Kind.PATCH, f"Patch {version}", detail=summary[:300], version_label=version, source_url=source_url,
                      verification=new, subject_kind=SubjectKind.PATCH, subject_id=patch.pk, occurred_at=None)  # fmt: skip
    patch.refresh_from_db()
    return patch


@transaction.atomic
def publish_requirement_fact(game: Game, *, fact, source_url: str) -> Requirement:
    existing = Requirement.objects.filter(
        game=game, platform=fact.platform, tier=fact.req_tier
    ).first()
    if (
        existing
        and not existing.is_placeholder
        and existing.verification == Verification.CONFIRMED
        and (
            (existing.cpu, existing.gpu, existing.ram_gb)
            != (fact.cpu or "", fact.gpu or "", fact.ram_gb)
        )
    ):
        raise FactDeferred("conflicts with confirmed requirements; needs human review")
    req, _ = Requirement.objects.update_or_create(
        game=game, platform=fact.platform, tier=fact.req_tier,
        defaults={"os": fact.os or "", "cpu": fact.cpu or "", "gpu": fact.gpu or "", "ram_gb": fact.ram_gb,
                  "storage_gb": fact.storage_gb, "source_url": source_url, "is_placeholder": False},
    )  # fmt: skip
    add_evidence(game, SubjectKind.REQUIREMENT, req.pk, source_url)
    old, new = recompute_verification(SubjectKind.REQUIREMENT, req.pk)
    record_change(game, Change.Kind.REQUIREMENT, f"{req.get_tier_display()} requirements {'published' if existing is None else 'updated'}",
                  detail=f"CPU {req.cpu or '-'} · GPU {req.gpu or '-'} · RAM {req.ram_gb or '-'} GB", source_url=source_url,
                  verification=new, subject_kind=SubjectKind.REQUIREMENT, subject_id=req.pk)  # fmt: skip
    return req


def try_auto_publish_fact(article: Article, cls) -> tuple[bool, str]:
    """Publish rules. Returns (published, reason-if-not)."""
    fact = cls.fact
    if fact is None:
        return False, "no structured fact"
    if not auto_publish_allowed():
        return False, "auto-publish disabled / kill switch"
    if cls.topic == "rumour":
        return False, "classified as rumour"
    if cls.confidence < settings.PB["AUTO_PUBLISH_THRESHOLD"]:
        return False, f"confidence {cls.confidence:.2f} below threshold"
    if not article.source_url:
        return False, "no source url"
    if fact.platform != "pc":
        return False, f"platform {fact.platform} is not PC"
    game = article.game
    try:
        if fact.kind == "release_date":
            publish_release_fact(
                game, date_=fact.release_date, source_url=article.source_url, platform=fact.platform
            )
        elif fact.kind == "patch":
            publish_patch_fact(
                game,
                version=fact.patch_version,
                date_=fact.patch_date,
                source_url=article.source_url,
                summary=cls.summary,
            )
        else:
            publish_requirement_fact(game, fact=fact, source_url=article.source_url)
    except FactDeferred as e:
        return False, str(e)
    request_revalidation(game_tags(game), [f"/games/{game.slug}", "/"])
    return True, ""


# ---------- articles ----------
def queue_for_review(article: Article, reason: str) -> None:
    article.status = Article.Status.QUEUED
    article.review_reason = reason[:300]
    article.save(update_fields=["status", "review_reason", "updated_at"])


@transaction.atomic
def approve_article(
    article: Article,
    user,
    *,
    title: str | None = None,
    summary: str | None = None,
    tags: list[str] | None = None,
) -> Article:
    if title is not None:
        article.title = title[:300]
    if summary is not None:
        article.our_summary = summary
    if tags is not None:
        article.tags = [t.strip().lower() for t in tags if t.strip()][:6]
    if not article.our_summary.strip():
        raise ValueError("an approved item needs our summary")
    add_evidence(article.game, SubjectKind.ARTICLE, article.pk, article.source_url)
    recompute_verification(SubjectKind.ARTICLE, article.pk)
    article.refresh_from_db(fields=["verification"])
    article.status = Article.Status.PUBLISHED
    article.published_at = timezone.now()
    article.reviewed_at, article.reviewed_by, article.updated_by = timezone.now(), user, user
    article.save()
    record_change(article.game, Change.Kind.NEWS, article.title, detail=article.our_summary[:300], source_url=article.source_url,
                  verification=article.verification, subject_kind=SubjectKind.ARTICLE, subject_id=article.pk)  # fmt: skip
    request_revalidation(
        [*game_tags(article.game), "news"], ["/news", f"/games/{article.game.slug}", "/"]
    )
    return article


@transaction.atomic
def reject_article(article: Article, user, reason: str = "") -> Article:
    was_published = article.status == Article.Status.PUBLISHED
    article.status = Article.Status.REJECTED
    article.review_reason = reason[:300] or article.review_reason
    article.reviewed_at, article.reviewed_by, article.updated_by = timezone.now(), user, user
    article.save()
    if was_published:
        Change.objects.filter(subject_kind=SubjectKind.ARTICLE, subject_id=article.pk).update(
            is_public=False
        )
        request_revalidation([*game_tags(article.game), "news"], ["/news"])
    return article


# ---------- videos ----------
def upsert_video(game: Game, source, item) -> tuple[Video | None, bool]:
    """Videos from sources flagged config.trusted_channel publish directly; others queue for review."""
    trusted = bool((source.config or {}).get("trusted_channel"))
    status = Video.Status.PUBLISHED if trusted and auto_publish_allowed() else Video.Status.QUEUED
    kind = Video.Kind.TRAILER if "trailer" in item.title.lower() else Video.Kind.OTHER
    video, created = Video.objects.get_or_create(
        game=game, youtube_id=item.external_id,
        defaults={"source": source, "title": item.title, "channel": item.channel, "kind": kind, "status": status,
                  "published_at": item.published_at},
    )  # fmt: skip
    if created and status == Video.Status.PUBLISHED:
        publish_video_side_effects(video)
    return video, created


def publish_video_side_effects(video: Video) -> None:
    add_evidence(
        video.game,
        SubjectKind.VIDEO,
        video.pk,
        f"https://www.youtube.com/watch?v={video.youtube_id}",
        Evidence.Kind.VIDEO,
    )
    record_change(video.game, Change.Kind.VIDEO, video.title, source_url=f"https://www.youtube.com/watch?v={video.youtube_id}",
                  verification=Verification.CONFIRMED, subject_kind=SubjectKind.VIDEO, subject_id=video.pk,
                  occurred_at=video.published_at)  # fmt: skip
    request_revalidation([*game_tags(video.game), "videos"], [f"/games/{video.game.slug}/videos"])


def approve_video(video: Video, user) -> None:
    video.status = Video.Status.PUBLISHED
    video.updated_by = user
    video.save()
    publish_video_side_effects(video)
