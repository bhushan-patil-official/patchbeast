"""Fetch -> normalise -> dedupe -> classify -> queue."""

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from llm.classify import Classification, ClassificationFailed, ItemForLLM, classify
from llm.factory import get_llm_client
from llm.guard import SpendGuard
from llm.ports import LLMUnavailable
from modules.common.urlutils import normalise_url, registrable_domain
from modules.content import services as content
from modules.content.models import Article, SubjectKind
from modules.games.models import Game
from modules.games.services import alias_terms, match_games
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


def find_near_duplicate(game: Game | None, h: int, window_days: int = 30) -> Article | None:
    """Per-game window; a general (game-less) source is compared against everything."""
    if h == 0:
        return None
    since = timezone.now() - timedelta(days=window_days)
    qs = Article.objects.filter(created_at__gte=since, simhash__isnull=False)
    if game is not None:
        qs = qs.filter(game=game)
    rows = qs.values_list("id", "simhash")[:2000]
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


def _top_game(hits: dict[str, int]) -> str | None:
    """The single clearly-best alias match, else None (ambiguous)."""
    if not hits:
        return None
    ranked = sorted(hits.items(), key=lambda kv: -kv[1])
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def ingest_items(source: Source, items: list[RawItem], *, dispatch: bool = True) -> IngestStats:
    stats = IngestStats()
    game = source.game  # None for a GENERAL feed: matched to a game by name below
    enabled = list(Game.objects.filter(enabled=True)) if game is None else []
    for item in items:
        stats.seen += 1
        if item.kind == "video":
            if game is None:
                continue  # videos need a known game
            _, created = content.upsert_video(game, source, item)
            stats.videos += int(created)
            continue
        try:
            canonical = normalise_url(item.url)
        except ValueError:
            stats.invalid += 1
            continue
        if Article.objects.filter(canonical_url=canonical).exists():
            stats.exact_dup += 1
            continue
        item_game = game
        if item_game is None:
            slug = _top_game(match_games(f"{item.title} {item.lead}", enabled))
            item_game = next((g for g in enabled if g.slug == slug), None)
        h = simhash64(f"{item.title} {item.lead}")
        dup = find_near_duplicate(item_game, h)
        reason = ""
        if dup:
            if registrable_domain(dup.source_url) == registrable_domain(item.url):
                stats.near_dup_skipped += 1  # repost on the same site
                continue
            if dup.game is not None:  # independent corroboration
                content.add_evidence(dup.game, SubjectKind.ARTICLE, dup.pk, item.url)
                content.recompute_verification(SubjectKind.ARTICLE, dup.pk)
            reason = f"possible duplicate of #{dup.pk} (different outlet)"
        article = Article.objects.create(
            game=item_game, source=source, title=item.title[:300], source_url=item.url, canonical_url=canonical,
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
@dataclass
class GameDecision:
    game: Game | None
    note: str = ""
    reject: bool = False


def resolve_game(
    article: Article, cls: Classification, games: dict[str, Game], alias_hits: dict[str, int]
) -> GameDecision:
    """Decide which game an article belongs to. Order of trust: agreement between the model and a
    name match > the source's own game > the model alone > a single name match > unassigned.
    A null/unsure model answer never overrides what the source already tells us."""
    src = article.source.game if article.source_id and article.source else None
    model = games.get(cls.game_slug) if cls.game_slug else None
    best = _top_game(alias_hits)

    if (
        cls.relevant is False
        and cls.confidence >= settings.PB["RELEVANCE_REJECT_THRESHOLD"]
        and not alias_hits
    ):
        return GameDecision(None, "not about a tracked game (auto-rejected)", reject=True)

    if model and (model.slug in alias_hits or src is None or model.pk == (src.pk if src else None)):
        return GameDecision(model)
    if src:
        note = ""
        if model and model.pk != src.pk:
            note = f"model suggested {model.name}, kept {src.name} (the source's game)"
        return GameDecision(src, note)
    if model:
        return GameDecision(model)
    if best and best in games:
        return GameDecision(games[best])
    names = ", ".join(sorted(alias_hits)) or "no name match"
    return GameDecision(None, f"no game matched ({names}): assign one")


def apply_classification(
    article: Article,
    cls: Classification,
    games: dict[str, Game] | None = None,
    alias_hits: dict[str, int] | None = None,
) -> None:
    games = games if games is not None else {g.slug: g for g in Game.objects.filter(enabled=True)}
    article.topic, article.confidence = cls.topic, cls.confidence
    article.tags, article.our_summary = cls.tags, cls.summary
    d = resolve_game(article, cls, games, alias_hits or {})
    if d.reject:
        article.status = Article.Status.REJECTED
        article.review_reason = d.note
        article.save()
        return
    if d.game is not None and d.game.pk != article.game_id:
        original_id, target = article.game_id, d.game
        article.game = target
        try:
            with transaction.atomic():
                article.save()
        except IntegrityError:  # the same URL is already filed under that game
            article.game_id = original_id
            d = GameDecision(
                games.get(article.game.slug) if article.game_id else None,
                f"could not move to {target.name} (already filed there)",
            )
    article.save()
    if d.game is None:
        content.queue_for_review(article, d.note)
        return
    published, why = content.try_auto_publish_fact(article, cls)
    if published and cls.fact:
        content.queue_for_review(
            article, f"fact auto-published ({cls.fact.kind}); approve to also list as news"
        )
    else:
        reason = article.review_reason or d.note or why or "needs human review"
        content.queue_for_review(article, reason)


def classify_article(article_id: int, lead: str, *, client=None) -> str:
    """Returns final state label. Idempotent: only acts on status=new."""
    article = Article.objects.select_related("game", "source", "source__game").get(pk=article_id)
    if article.status != Article.Status.NEW:
        return "skipped"
    if platform.kill_switch_on():
        return "paused"
    game_objs = list(Game.objects.filter(enabled=True))
    games = {g.slug: g for g in game_objs}
    alias_hits = match_games(f"{article.title} {lead}", game_objs)
    llm = client or SpendGuard(get_llm_client())
    item = ItemForLLM(
        title=article.title, lead=lead, url=article.source_url, source_name=article.source_name
    )
    try:
        cls = classify(
            llm,
            item,
            {s: g.name for s, g in games.items()},
            {s: alias_terms(g) for s, g in games.items()},
        )
    except LLMUnavailable as e:
        _attach_by_name(article, games, alias_hits)
        content.queue_for_review(article, f"LLM unavailable: {e}")
        return "queued-unavailable"
    except ClassificationFailed as e:
        _attach_by_name(article, games, alias_hits)
        content.queue_for_review(article, e.reason)
        return "queued-invalid"
    apply_classification(article, cls, games, alias_hits)
    return "classified"


def _attach_by_name(article: Article, games: dict[str, Game], hits: dict[str, int]) -> None:
    """Without a model answer, a clear name match still attaches an unassigned article."""
    if article.game_id is None and (slug := _top_game(hits)) and slug in games:
        article.game = games[slug]
        try:
            with transaction.atomic():
                article.save()
        except IntegrityError:
            article.game = None


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
