"""Game/Release writes. Business rules for the release timeline live here."""

import re
from collections.abc import Iterable
from datetime import date

from django.db import transaction

from .models import Game, Release


@transaction.atomic
def set_current_release(
    game: Game,
    *,
    date_: date | None,
    confidence: str,
    source_url: str = "",
    source_count: int = 0,
    platform: str = "pc",
    is_placeholder: bool = False,
    note: str = "",
    user=None,
) -> tuple[Release, Release | None]:
    """Replace the current release row (history kept). Returns (new, previous)."""
    prev = (
        Release.objects.select_for_update()
        .filter(game=game, platform=platform, is_current=True)
        .first()
    )
    if prev:
        prev.is_current = False
        prev.save(update_fields=["is_current", "updated_at"])
    new = Release.objects.create(
        game=game, platform=platform, date=date_, confidence=confidence, source_url=source_url,
        source_count=source_count, is_current=True, is_placeholder=is_placeholder, note=note,
        created_by=user, updated_by=user,
    )  # fmt: skip
    return new, prev


def alias_terms(game: Game) -> list[str]:
    """Names a headline may use for this game. The short name only counts when it is distinctive."""
    raw = [game.name, *(game.aliases or [])]
    if len(game.short_name or "") >= 5:
        raw.append(game.short_name)
    terms = []
    for t in raw:
        t = re.sub(r"\(.*?\)", "", str(t)).strip().lower()
        if len(t) >= 3 and t not in terms:
            terms.append(t)
    return terms


def match_games(text: str, games: Iterable[Game]) -> dict[str, int]:
    """Count distinct whole-word mentions per game slug (overlapping aliases of one mention count once)."""
    hay = (text or "").lower()
    hits: dict[str, int] = {}
    for g in games:
        spans: list[tuple[int, int]] = []
        for t in alias_terms(g):
            spans += [
                m.span() for m in re.finditer(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", hay)
            ]
        merged: list[list[int]] = []
        for start, end in sorted(spans):
            if merged and start < merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        if merged:
            hits[g.slug] = len(merged)
    return hits
