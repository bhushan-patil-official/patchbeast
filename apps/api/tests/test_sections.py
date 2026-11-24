from datetime import date, timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from modules.content import services as content
from modules.content.models import Article, Change, Patch
from modules.games.models import Game, Release


@pytest.fixture
def mg(db):
    return Game.objects.create(slug="mg", name="MG", hub_config={"platforms": ["pc", "ps5"]})


def mk_patch(
    game,
    platform="ps5",
    version="1.0.1",
    sources=("https://a.example.com/p", "https://b.example.org/p"),
    **kw,
):
    p = Patch.objects.create(game=game, platform=platform, version=version, date=date(2026, 11, 20),
                             our_summary=kw.pop("summary", "Our summary."), **kw)  # fmt: skip
    for u in sources:
        content.add_evidence(game, "patch", p.pk, u)
    content.recompute_verification("patch", p.pk)
    return p


def test_patch_detail_endpoint(client, mg):
    mk_patch(mg, "ps5", highlights=["Fixes a crash"], size_note="604 MB")
    mk_patch(mg, "pc", sources=("https://a.example.com/pc",))
    d = client.get("/api/v1/games/mg/patches/ps5/1.0.1/").json()
    assert d["patch"]["highlights"] == ["Fixes a crash"] and d["patch"]["size_note"] == "604 MB"
    assert d["patch"]["verification"] == "confirmed" and len(d["sources"]) == 2
    assert {s["domain"] for s in d["sources"]} == {"example.com", "example.org"}
    assert [p["platform"] for p in d["siblings"]] == ["pc"]  # same version on another platform
    assert d["seo"]["indexable"] is True


def test_patch_detail_404_and_dotted_versions(client, mg):
    assert client.get("/api/v1/games/mg/patches/ps5/9.9.9/").status_code == 404
    mk_patch(mg, "ps5", version="01.002.002")
    assert client.get("/api/v1/games/mg/patches/ps5/01.002.002/").status_code == 200


def test_unsourced_patch_page_is_noindex(client, mg):
    mk_patch(mg, "ps5", sources=())
    assert client.get("/api/v1/games/mg/patches/ps5/1.0.1/").json()["seo"]["indexable"] is False


def test_placeholder_patch_page_is_noindex(client, mg):
    p = mk_patch(mg, "ps5")
    Patch.objects.filter(pk=p.pk).update(is_placeholder=True)
    assert client.get("/api/v1/games/mg/patches/ps5/1.0.1/").json()["seo"]["indexable"] is False


def test_timeline_endpoint_is_paginated_and_per_game(client, mg, game):
    for i in range(25):
        content.record_change(mg, "patch", f"c{i}", verification="confirmed")
    content.record_change(game, "patch", "other game", verification="confirmed")
    r = client.get("/api/v1/games/mg/changes/").json()
    assert r["count"] == 25 and len(r["results"]) == 20 and r["next"]
    assert all(c["game_slug"] == "mg" for c in r["results"])
    assert client.get("/api/v1/games/nope/changes/").status_code == 404


def test_news_filter_per_game(client, mg, game):
    for g, n in ((mg, "mg-news"), (game, "other-news")):
        Article.objects.create(game=g, title=n, source_url=f"https://x.example.com/{n}", canonical_url=f"https://x.example.com/{n}",
                               status="published", our_summary="s", published_at=timezone.now())  # fmt: skip
    r = client.get("/api/v1/news/?game=mg").json()
    assert [a["title"] for a in r["results"]] == ["mg-news"]


def test_sitemap_lists_section_pages_only_when_real(client, mg):
    Release.objects.create(
        game=mg,
        platform="ps5",
        date=date.today() - timedelta(days=3),
        confidence="confirmed",
        source_url="https://a.example.com",
    )
    paths = {e["path"] for e in client.get("/api/v1/sitemap/").json()}
    assert "/games/mg/news" not in paths and "/games/mg/timeline" not in paths
    mk_patch(mg, "ps5")
    Article.objects.create(game=mg, title="n", source_url="https://x.example.com/n", canonical_url="https://x.example.com/n",
                           status="published", our_summary="s", published_at=timezone.now())  # fmt: skip
    content.record_change(mg, "patch", "c", verification="confirmed")
    paths = {e["path"] for e in client.get("/api/v1/sitemap/").json()}
    assert {"/games/mg/news", "/games/mg/timeline", "/games/mg/patches/ps5/1.0.1"} <= paths


def test_patch_fact_records_change_dated_on_patch_date(mg):
    content.publish_patch_fact(mg, version="2.0", date_=date(2026, 11, 20), source_url="https://a.example.com/x", summary="s", platform="ps5",
                               highlights=["a", "b"], size_note="1 GB")  # fmt: skip
    c = Change.objects.get(version_label="2.0")
    assert c.occurred_at.date() == date(2026, 11, 20)
    assert Patch.objects.get(version="2.0").highlights == ["a", "b"]


# ---- content pack loader ----
@pytest.fixture
def gta(db):
    return Game.objects.create(
        slug="gta-6-pc",
        name="Grand Theft Auto VI",
        hub_config={"platforms": ["pc", "ps5", "xbox_series"]},
    )


def test_pack_dry_run_saves_nothing(gta):
    call_command("load_pack", "gta6", "--dry-run")
    assert (
        not Patch.objects.exists() and not Release.objects.exists() and not Article.objects.exists()
    )


def test_pack_loads_sourced_content_and_is_idempotent(gta):
    call_command("load_pack", "gta6")
    call_command("load_pack", "gta6")
    assert Patch.objects.count() == 6 and Article.objects.count() == 2
    p = Patch.objects.get(version="01.002.002", platform="ps5")
    assert (
        p.verification == "confirmed"
        and p.source_count == 3
        and p.size_note == "about 604 MB"
        and len(p.highlights) == 5
    )
    assert Patch.objects.get(version="01.002.000", platform="ps5").verification == "reported"
    rel = {r.platform: r for r in Release.objects.filter(game=gta, is_current=True)}
    assert rel["ps5"].date == date(2026, 11, 19) and rel["ps5"].confidence == "confirmed"
    assert "pc" not in rel  # no PC date is ever invented
    assert all(a.status == "published" and a.our_summary for a in Article.objects.all())
    assert Change.objects.filter(
        version_label="01.002.002", title="Patch 01.002.002 (PS5)"
    ).exists()


def test_pack_requires_game(db):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("load_pack", "gta6")
