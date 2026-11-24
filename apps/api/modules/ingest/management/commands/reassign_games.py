"""Re-evaluate queued articles that were stuck with a stale game-assignment reason.

Old behaviour queued an article whenever the model was unsure ("model could not assign a game") or
disagreed with the source ("model assigned a different game"). This re-applies the current rules
(alias name match + source trust) to those items and clears the stale reason. Safe to re-run."""

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.models import Q

from modules.content.models import Article
from modules.games.models import Game
from modules.games.services import match_games
from modules.ingest.services import _top_game

STALE = Q(review_reason__icontains="could not assign a game") | Q(
    review_reason__icontains="assigned a different game"
)


class Command(BaseCommand):
    help = "reassign_games [--dry-run]: fix queued articles stuck on an old game-assignment reason"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dry_run=False, **opts):
        games = list(Game.objects.filter(enabled=True))
        by_slug = {g.slug: g for g in games}
        moved = cleared = unresolved = 0
        for a in (
            Article.objects.filter(status=Article.Status.QUEUED)
            .filter(STALE)
            .select_related("game")
        ):
            slug = _top_game(match_games(f"{a.title} {a.our_summary}", games))
            target = by_slug.get(slug) if slug else None
            note = ""
            if target and (a.game is None or a.game.pk != target.pk):
                if not dry_run:
                    a.game = target
                    try:
                        with transaction.atomic():
                            a.save()
                    except IntegrityError:
                        a.game, target = Article.objects.get(pk=a.pk).game, None
                if target:
                    moved += 1
                    note = f"moved to {target.name} (name match)"
            if not note:
                if a.game is None:
                    unresolved += 1
                    note = "no game matched: assign one"
                else:
                    cleared += 1
                    note = f"game kept from the source ({a.game.name})"
            if not dry_run:
                a.review_reason = note
                a.save(update_fields=["review_reason", "updated_at"])
        verb = "would change" if dry_run else "changed"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb}: {moved} moved by name, {cleared} kept with the source's game, {unresolved} still need a game"
            )
        )
