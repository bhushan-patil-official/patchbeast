"""Seed script. Placeholder data ONLY: nothing here is a claim of fact; every row is flagged and noindex."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.common.choices import Verification
from modules.content import services as content
from modules.content.models import Article, Change, Patch, Requirement, SubjectKind, Video
from modules.games.models import Game, Release
from modules.platform.models import FeatureFlag, SiteSetting
from modules.sources.models import Source

ANCHOR = "gta-6-pc"


def seed_anchor() -> Game:
    game, _ = Game.objects.update_or_create(
        slug=ANCHOR,
        defaults={
            "name": "Grand Theft Auto VI (PC)",
            "short_name": "GTA VI · PC",
            "tagline": "PC launch tracker (placeholder entry: nothing here is verified yet)",
            "platform": "pc",
            "is_placeholder": True,
            "hub_config": {
                "sections": ["release", "requirements", "patches", "videos", "news"],
                "checker": True,
                "affiliate_categories": ["gpu", "ssd", "ram"],
                "faq": [
                    {
                        "q": "Is there a confirmed PC release date?",
                        "a": "This tracker only shows a date once it carries a source link and a verification status. Until then it reads 'Date unconfirmed'.",
                    }
                ],
            },
        },
    )
    if not Release.objects.filter(game=game, is_current=True).exists():
        Release.objects.create(game=game, platform="pc", date=None, confidence=Verification.RUMOUR, is_placeholder=True,
                               note="PLACEHOLDER: no release date has been verified.")  # fmt: skip
    for tier in ("min", "rec"):
        Requirement.objects.get_or_create(game=game, platform="pc", tier=tier,
                                          defaults={"is_placeholder": True, "notes": "PLACEHOLDER: requirements not published."})  # fmt: skip
    placeholders = [
        ("PLACEHOLDER official newsroom feed", Source.Type.RSS, "https://example.invalid/replace-with-official-feed.xml", {}),
        ("PLACEHOLDER official YouTube channel", Source.Type.YOUTUBE, "", {"channel_id": "UCREPLACE_WITH_REAL_CHANNEL_ID", "trusted_channel": False}),
        ("PLACEHOLDER PC store patch-notes API", Source.Type.API, "https://example.invalid/replace-with-api.json",
         {"items_path": "items", "title_field": "title", "url_field": "url", "date_field": "date"}),
    ]  # fmt: skip
    for name, typ, url, cfg in placeholders:
        Source.objects.get_or_create(game=game, name=name, defaults={"type": typ, "url": url, "config": cfg, "enabled": False, "is_placeholder": True})
    return game


def seed_demo() -> Game:
    now = timezone.now()
    game, _ = Game.objects.update_or_create(
        slug="demo-launch",
        defaults={
            "name": "Demo Launch (sample data)", "short_name": "DEMO", "tagline": "Sample data to preview the UI. Not a real game. noindex.",
            "is_placeholder": True, "allow_index": False, "sort_order": 99,
            "hub_config": {"checker": True, "faq": [{"q": "Is this real?", "a": "No. Every item on this page is DEMO data."}]},
        },
    )  # fmt: skip
    if not Release.objects.filter(game=game, is_current=True, date__isnull=False).exists():
        Release.objects.filter(game=game).update(is_current=False)
        Release.objects.create(game=game, platform="pc", date=(now + timedelta(days=90)).date(), confidence=Verification.REPORTED,
                               source_url="https://example.com/demo-release", source_count=1, note="DEMO data")  # fmt: skip
    Requirement.objects.update_or_create(game=game, platform="pc", tier="min", defaults={
        "os": "Windows 10 64-bit", "cpu": "Intel Core i5-8400 / AMD Ryzen 5 1600", "gpu": "NVIDIA GTX 1060 6GB / AMD RX 580 8GB",
        "ram_gb": 8, "storage_gb": 60, "cpu_ref": "intel-i5-8400", "gpu_ref": "nvidia-gtx-1060-6gb", "notes": "DEMO data",
        "source_url": "https://example.com/demo-requirements", "verification": Verification.REPORTED, "source_count": 1})  # fmt: skip
    Requirement.objects.update_or_create(game=game, platform="pc", tier="rec", defaults={
        "os": "Windows 11 64-bit", "cpu": "Intel Core i7-9700K / AMD Ryzen 5 3600", "gpu": "NVIDIA RTX 3060 / AMD RX 6600 XT",
        "ram_gb": 16, "storage_gb": 60, "cpu_ref": "amd-ryzen-5-3600", "gpu_ref": "nvidia-rtx-3060", "notes": "DEMO data",
        "source_url": "https://example.com/demo-requirements", "verification": Verification.REPORTED, "source_count": 1})  # fmt: skip
    for i, (ver, days) in enumerate([("0.9.0", 21), ("0.9.1", 7)]):
        p, created = Patch.objects.get_or_create(game=game, version=ver, defaults={
            "date": (now - timedelta(days=days)).date(), "notes_url": "https://example.com/demo-patch",
            "our_summary": f"DEMO: sample patch {ver} fixing placeholder issues.", "verification": Verification.CONFIRMED, "source_count": 2})  # fmt: skip
        if created:
            content.record_change(game, Change.Kind.PATCH, f"Patch {ver}", detail=p.our_summary, version_label=ver, source_url=p.notes_url,
                                  verification=Verification.CONFIRMED, subject_kind=SubjectKind.PATCH, subject_id=p.pk,
                                  occurred_at=now - timedelta(days=days))  # fmt: skip
    Video.objects.get_or_create(game=game, youtube_id="aqz-KE-bpKQ", defaults={
        "title": "DEMO: sample video (open-licence film)", "channel": "Blender", "kind": Video.Kind.TRAILER,
        "status": Video.Status.PUBLISHED, "published_at": now - timedelta(days=3), "is_placeholder": False})  # fmt: skip
    for i in (1, 2):
        a, created = Article.objects.get_or_create(game=game, canonical_url=f"https://example.com/demo-news-{i}", defaults={
            "title": f"DEMO headline {i}", "source_url": f"https://example.com/demo-news-{i}", "source_name": "example.com",
            "our_summary": "DEMO: this is our own short summary of a sample item. It links to its source and shows its verification status.",
            "tags": ["demo"], "topic": "news", "status": Article.Status.PUBLISHED, "verification": Verification.REPORTED,
            "published_at": now - timedelta(days=i), "confidence": 0.9})  # fmt: skip
        if created:
            content.record_change(game, Change.Kind.NEWS, a.title, detail=a.our_summary, source_url=a.source_url,
                                  verification=Verification.REPORTED, subject_kind=SubjectKind.ARTICLE, subject_id=a.pk,
                                  occurred_at=a.published_at)  # fmt: skip
    return game


class Command(BaseCommand):
    help = "Seed the placeholder launch anchor, flags and settings. --demo adds clearly-labelled demo content (noindex)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true")

    def handle(self, *args, demo=False, **opts):
        SiteSetting.load()
        for key, note in [("ads", "Ad slots"), ("affiliate", "Affiliate hardware blocks"), ("newsletter", "Newsletter signup + digest"),
                          ("tier2_cheats", "Tier 2: cheats"), ("tier2_maps", "Tier 2: maps"), ("tier3_alerts", "Tier 3: alerts")]:  # fmt: skip
            FeatureFlag.objects.get_or_create(key=key, defaults={"enabled": key == "newsletter", "note": note})
        seed_anchor()
        self.stdout.write(self.style.SUCCESS(f"seeded anchor '{ANCHOR}' (placeholder, noindex)"))
        if demo:
            seed_demo()
            self.stdout.write(self.style.SUCCESS("seeded DEMO game 'demo-launch' (noindex)"))
