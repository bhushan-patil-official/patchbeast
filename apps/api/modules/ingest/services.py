"""Fetch -> normalise -> dedupe -> classify -> queue."""

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from llm.classify import Classification, ClassificationFailed, ItemForLLM, classify
from llm.factory import get_llm_client
from llm.guard import SpendGuard
from llm.ports import LLMUnavailable
from modules.common.urlutils import normalise_url, registrable_domain
from modules.content import services as content
from modules.content.models import Article, SubjectKind
from modules.games.models import Game
from modules.platform import services as platform
from modules.sources import services as source_services
from modules.sources.models import Source
from modules.sources.ports import FetchError, RawItem
from modules.sources.registry import get_fetcher

from .models import FetchLog

log = logging.getLogger(__name__)


# ---------- near-duplicate detection (64-bit simhash) ----------
def simhash64(text: str) -> int:
    tokens = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]
    if len(tokens) < 4:
        return 0
    acc = [0] * 64
    for tok in tokens:
        h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "big")
        for i in range(64):
            acc[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i in range(64) if acc[i] > 0)


def to_signed(h: int) -> int:
    return h - (1 << 64) if h >= (1 << 63) else h


def to_unsigned(h: int) -> int:
    return h + (1 << 64) if h < 0 else h


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def find_near_duplicate(game: Game, h: int, window_days: int = 30) -> Article | None:
    if h == 0:
        return None
    since = timezone.now() - timedelta(days=window_days)
    rows = Article.objects.filter(
        game=game, created_at__gte=since, simhash__isnull=False
    ).values_list("id", "simhash")[:2000]
    limit = settings.PB["NEAR_DUP_HAMMING"]
    for pk, sh in rows:
        if sh is not None and hamming(h, to_unsigned(sh)) <= limit:
            return Article.objects.get(pk=pk)
    return None


# ---------- ingest ----------
@dataclass
class IngestStats:
    seen: int = 0
    new: int = 0
    exact_dup: int = 0
    near_dup_skipped: int = 0
    videos: int = 0
    invalid: int = 0
    created: list = field(default_factory=list)  # [(article_id, lead)]


def ingest_items(source: Source, items: list[RawItem], *, dispatch: bool = True) -> IngestStats:
    stats = IngestStats()
    game = source.game
    for item in items:
        stats.seen += 1
        if item.kind == "video":
            _, created = content.upsert_video(game, source, item)
            stats.videos += int(created)
            continue
        try:
            canonical = normalise_url(item.url)
        except ValueError:
            stats.invalid += 1
            continue
        if Article.objects.filter(game=game, canonical_url=canonical).exists():
            stats.exact_dup += 1
            continue
        h = simhash64(f"{item.title} {item.lead}")
        dup = find_near_duplicate(game, h)
        reason = ""
        if dup:
            if registrable_domain(dup.source_url) == registrable_domain(item.url):
                stats.near_dup_skipped += 1  # repost on the same site
                continue
            content.add_evidence(
                game, SubjectKind.ARTICLE, dup.pk, item.url
            )  # independent corroboration
            content.recompute_verification(SubjectKind.ARTICLE, dup.pk)
            reason = f"possible duplicate of #{dup.pk} (different outlet)"
        article = Article.objects.create(
            game=game, source=source, title=item.title[:300], source_url=item.url, canonical_url=canonical,
            source_name=source.name, source_published_at=item.published_at, simhash=to_signed(h) if h else None,
            status=Article.Status.NEW, review_reason=reason,
        )  # fmt: skip
        stats.new += 1
        stats.created.append((article.pk, item.lead))
    if dispatch:
        from .tasks import classify_article_task

        for pk, lead in stats.created:
            classify_article_task.delay(pk, lead)
    return stats


def fetch_and_ingest(source_id: int, *, fetcher=None) -> IngestStats | None:
    if platform.kill_switch_on():
        return None
    source = Source.objects.select_related("game").get(pk=source_id)
    if not source.enabled:
        return None
    t0 = time.monotonic()
    try:
        result = (fetcher or get_fetcher(source.type)).fetch(source_services.to_spec(source))
    except FetchError as e:
        source_services.mark_failure(
            source, str(e), retry_after=e.retry_after, permanent=e.permanent
        )
        FetchLog.objects.create(
            source=source,
            ok=False,
            error=str(e)[:500],
            duration_ms=int((time.monotonic() - t0) * 1000),
        )
        return None
    stats = ingest_items(source, result.items)
    source_services.mark_success(source, result)
    FetchLog.objects.create(
        source=source, ok=True, not_modified=result.not_modified, items_seen=stats.seen, items_new=stats.new,
        duration_ms=int((time.monotonic() - t0) * 1000),
    )  # fmt: skip
    return stats


# ---------- classify ----------
def apply_classification(article: Article, cls: Classification) -> None:
    article.topic = cls.topic
    article.confidence = cls.confidence
    article.tags = cls.tags
    article.our_summary = cls.summary
    if cls.game_slug and cls.game_slug != article.game.slug:
        article.save()
        content.queue_for_review(article, f"model assigned a different game ({cls.game_slug})")
        return
    if cls.game_slug is None:
        article.save()
        content.queue_for_review(article, "model could not assign a game")
        return
    article.save()
    published, why = content.try_auto_publish_fact(article, cls)
    if published and cls.fact:
        content.queue_for_review(
            article, f"fact auto-published ({cls.fact.kind}); approve to also list as news"
        )
    else:
        content.queue_for_review(article, article.review_reason or why or "needs human review")


def classify_article(article_id: int, lead: str, *, client=None) -> str:
    """Returns final state label. Idempotent: only acts on status=new."""
    article = Article.objects.select_related("game", "source").get(pk=article_id)
    if article.status != Article.Status.NEW:
        return "skipped"
    if platform.kill_switch_on():
        return "paused"
    games = dict(Game.objects.filter(enabled=True).values_list("slug", "name"))
    llm = client or SpendGuard(get_llm_client())
    item = ItemForLLM(
        title=article.title, lead=lead, url=article.source_url, source_name=article.source_name
    )
    try:
        cls = classify(llm, item, games)
    except LLMUnavailable as e:
        content.queue_for_review(article, f"LLM unavailable: {e}")
        return "queued-unavailable"
    except ClassificationFailed as e:
        content.queue_for_review(article, e.reason)
        return "queued-invalid"
    apply_classification(article, cls)
    return "classified"


def requeue_stuck(minutes: int = 30) -> int:
    """Articles stuck in NEW (lost task / worker crash) are never dropped: send to review."""
    if platform.kill_switch_on():
        return 0
    cutoff = timezone.now() - timedelta(minutes=minutes)
    n = 0
    for a in Article.objects.filter(status=Article.Status.NEW, created_at__lt=cutoff):
        content.queue_for_review(a, a.review_reason or "classification did not complete")
        n += 1
    return n
