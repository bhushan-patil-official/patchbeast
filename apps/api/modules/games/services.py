"""Game/Release writes. Business rules for the release timeline live here."""

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
