"""Load a sourced content pack (content_packs/<name>.json): releases, patches, news.

Everything is created through the normal content services, so verification is computed from the
distinct sources listed (>= 2 independent domains = Confirmed). Idempotent. Use --dry-run first."""

import json
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.common.platforms import label
from modules.common.urlutils import normalise_url
from modules.content import services as content
from modules.content.models import Article, SubjectKind
from modules.games.models import Game


class Command(BaseCommand):
    help = (
        "load_pack <name> [--dry-run]: load a sourced content pack from content_packs/<name>.json"
    )

    def add_arguments(self, parser):
        parser.add_argument("name")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, name, dry_run=False, **opts):
        path = Path(settings.BASE_DIR) / "content_packs" / f"{name}.json"
        if not path.exists():
            raise CommandError(f"no such pack: {path}")
        pack = json.loads(path.read_text())
        game = Game.objects.filter(slug=pack["game_slug"]).first()
        if game is None:
            raise CommandError(f"game {pack['game_slug']!r} not found: run `manage.py seed` first")
        self.stdout.write(self.style.WARNING(pack.get("notice", "")))
        try:
            with transaction.atomic():
                self._load(game, pack)
                if dry_run:
                    raise _Rollback
        except _Rollback:
            self.stdout.write(self.style.WARNING("dry run: nothing was saved"))

    def _load(self, game: Game, pack: dict) -> None:
        for r in pack.get("releases", []):
            for url in r["sources"]:
                content.publish_release_fact(
                    game,
                    date_=date.fromisoformat(r["date"]),
                    source_url=url,
                    platform=r["platform"],
                )
            self.stdout.write(
                f"release {label(r['platform'])}: {r['date']} ({len(r['sources'])} sources)"
            )
        for p in pack.get("patches", []):
            for plat in p["platforms"]:
                first, *rest = p["sources"]
                patch = content.publish_patch_fact(
                    game, version=p["version"], date_=date.fromisoformat(p["date"]), source_url=first,
                    summary=p["summary"], platform=plat, highlights=p.get("highlights", []),
                    size_note=(p.get("size_note") or {}).get(plat, ""),
                )  # fmt: skip
                for url in rest:
                    content.add_evidence(game, SubjectKind.PATCH, patch.pk, url)
                content.recompute_verification(SubjectKind.PATCH, patch.pk)
                patch.refresh_from_db()
                self.stdout.write(
                    f"patch {p['version']} {label(plat)}: {patch.verification} ({patch.source_count} sources)"
                )
        for a in pack.get("articles", []):
            canonical = normalise_url(a["source_url"])
            art, created = Article.objects.get_or_create(
                game=game, canonical_url=canonical,
                defaults={"title": a["title"], "source_url": a["source_url"], "source_name": a.get("source_name", ""),
                          "status": Article.Status.QUEUED, "topic": "news"},
            )  # fmt: skip
            if art.status != Article.Status.PUBLISHED:
                content.approve_article(
                    art, None, title=a["title"], summary=a["summary"], tags=a.get("tags", [])
                )
            self.stdout.write(f"article: {a['title']} ({'new' if created else 'existing'})")
        self.stdout.write(self.style.SUCCESS("pack loaded"))


class _Rollback(Exception):
    pass
