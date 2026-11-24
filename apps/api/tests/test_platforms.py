from datetime import date, timedelta

import pytest
from django.core import mail
from django.core.exceptions import ValidationError

from llm.classify import Fact
from modules.common.platforms import normalise_platform
from modules.content import services as content
from modules.content.models import Article, Change, Patch
from modules.games.models import Game, Release
from modules.newsletter import services as nl
from modules.newsletter.models import Subscriber

from .test_publish_rules import DATE, art, cls


@pytest.fixture
def multi(db):
    return Game.objects.create(
        slug="multi", name="Multi", vanity_path="Multi-Tracker",
        hub_config={"platforms": ["ps5", "pc", "xbox_series"]},
    )  # fmt: skip


def test_normalise_platform_aliases():
    assert normalise_platform("PlayStation 5") == "ps5"
    assert normalise_platform("Xbox Series X") == "xbox_series"
    assert normalise_platform("Steam") == "pc"
    assert normalise_platform("Dreamcast") == "other"
    assert (
        Fact(kind="release_date", platform="PS5", release_date=date(2027, 1, 1)).platform == "ps5"
    )


def test_game_platforms_pc_first_and_default(db, multi):
    assert multi.platforms == ["pc", "ps5", "xbox_series"]
    assert Game.objects.create(slug="solo", name="Solo").platforms == ["pc"]


def test_vanity_path_normalised_unique_and_reserved(multi):
    assert multi.vanity_path == "multi-tracker"
    bad = Game(slug="x", name="X", vanity_path="news")
    with pytest.raises(ValidationError):
        bad.full_clean()
    a = Game.objects.create(slug="a", name="A", vanity_path="")
    b = Game.objects.create(slug="b", name="B", vanity_path="")
    assert a.vanity_path is None and b.vanity_path is None  # blanks do not collide


def test_console_release_auto_published_per_platform(multi):
    ps5 = Fact(kind="release_date", platform="ps5", release_date=date(2027, 5, 5))
    assert content.try_auto_publish_fact(
        art(multi, "https://a.example.com/1"), cls(ps5, slug="multi")
    )[0]
    assert content.try_auto_publish_fact(
        art(multi, "https://b.example.org/2"), cls(DATE, slug="multi")
    )[0]
    rows = {r.platform: r for r in Release.objects.filter(game=multi, is_current=True)}
    assert rows["ps5"].date == date(2027, 5, 5) and rows["pc"].date == date(2027, 3, 1)
    assert Change.objects.filter(game=multi, title="Release date updated (PS5)").exists()


def test_untracked_or_unknown_platform_goes_to_review(multi, game):
    sw = Fact(kind="release_date", platform="switch2", release_date=date(2027, 5, 5))
    assert (
        "not tracked"
        in content.try_auto_publish_fact(
            art(multi, "https://a.example.com/1"), cls(sw, slug="multi")
        )[1]
    )
    other = Fact(kind="release_date", platform="other", release_date=date(2027, 5, 5))
    assert not content.try_auto_publish_fact(art(game, "https://a.example.com/2"), cls(other))[0]


def test_requirements_are_pc_only(multi):
    r = Fact(kind="requirement", platform="ps5", req_tier="min", cpu="x", gpu="y")
    ok, why = content.try_auto_publish_fact(
        art(multi, "https://a.example.com/r"), cls(r, slug="multi", topic="requirements")
    )
    assert not ok and "PC only" in why


def test_patches_are_per_platform_and_filterable(client, multi):
    for plat in ("pc", "ps5"):
        content.publish_patch_fact(
            multi,
            version="1.0.1",
            date_=date(2027, 1, 1),
            source_url=f"https://{plat}.example.com/p",
            summary="s",
            platform=plat,
        )
    assert Patch.objects.filter(game=multi, version="1.0.1").count() == 2
    assert Change.objects.filter(title="Patch 1.0.1 (PS5)").exists()
    allp = client.get("/api/v1/games/multi/patches/").json()
    assert {p["platform"] for p in allp["items"]} == {"pc", "ps5"} and allp[
        "selected_platform"
    ] == ""
    only = client.get("/api/v1/games/multi/patches/?platform=ps5").json()
    assert [p["platform"] for p in only["items"]] == ["ps5"] and only["selected_platform"] == "ps5"
    assert (
        client.get("/api/v1/games/multi/patches/?platform=bogus").json()["selected_platform"] == ""
    )
    assert [p["id"] for p in allp["platforms"]] == ["pc", "ps5", "xbox_series"]


def test_hub_exposes_releases_per_platform_primary_first(client, multi):
    Release.objects.create(
        game=multi,
        platform="ps5",
        date=date.today() + timedelta(days=50),
        confidence="confirmed",
        source_url="https://a.example.com",
    )
    Release.objects.create(game=multi, platform="pc", date=None, confidence="rumour")
    h = client.get("/api/v1/games/multi/").json()
    assert [r["platform"] for r in h["releases"]] == ["pc", "ps5"]
    assert h["release"]["platform"] == "pc" and h["release"]["countdown_mode"] == "unconfirmed"
    assert h["releases"][1]["countdown_mode"] == "live"
    assert h["game"]["path"] == "/multi-tracker" and h["game"]["vanity_path"] == "multi-tracker"
    assert h["seo"]["indexable"] is True  # a real console date counts as real content


def test_sitemap_uses_vanity_path_for_hub(client, multi):
    Release.objects.create(
        game=multi,
        platform="ps5",
        date=date.today() + timedelta(days=5),
        confidence="reported",
        source_url="https://a.example.com",
    )
    Patch.objects.create(game=multi, version="1")
    paths = {e["path"] for e in client.get("/api/v1/sitemap/").json()}
    assert (
        "/multi-tracker" in paths
        and "/games/multi" not in paths
        and "/games/multi/patches" in paths
    )


def test_seo_overrides_from_hub_config(client, db):
    Game.objects.create(
        slug="s",
        name="S",
        hub_config={"seo_title": "Custom title", "seo_description": "Custom desc"},
    )
    h = client.get("/api/v1/games/s/").json()
    assert (h["seo_title"], h["seo_description"]) == ("Custom title", "Custom desc")


# ---- per-game newsletter ----
def confirmed(email, games=None):
    return Subscriber.objects.create(email=email, confirmed=True, games=games or [])


def test_subscribe_from_game_page_narrows_digest(db, multi, game):
    nl.subscribe("a@example.com", game="multi")
    assert Subscriber.objects.get(email="a@example.com").games == ["multi"]
    nl.subscribe("b@example.com", game="does-not-exist")  # unknown game ignored => all games
    assert Subscriber.objects.get(email="b@example.com").games == []


def test_digest_filtered_to_subscribed_games(db, multi, game):
    content.record_change(multi, "patch", "Multi patch", verification="confirmed")
    content.record_change(game, "patch", "Other game patch", verification="confirmed")
    only, everyone, other = (
        confirmed("o@example.com", ["multi"]),
        confirmed("e@example.com"),
        confirmed("x@example.com", ["test-game"]),
    )
    week = nl.iso_week()
    for s in (only, everyone, other):
        assert nl.send_digest_to(s, week)
    bodies = {m.to[0]: m.body for m in mail.outbox}
    assert (
        "Multi patch" in bodies["o@example.com"]
        and "Other game patch" not in bodies["o@example.com"]
    )
    assert (
        "Multi patch" in bodies["e@example.com"] and "Other game patch" in bodies["e@example.com"]
    )
    assert (
        "Other game patch" in bodies["x@example.com"]
        and "Multi patch" not in bodies["x@example.com"]
    )


def test_no_changes_for_my_games_sends_nothing(db, multi, game):
    content.record_change(game, "patch", "Other", verification="confirmed")
    s = confirmed("o@example.com", ["multi"])
    assert nl.send_digest_to(s, nl.iso_week()) is False and not mail.outbox
    s.refresh_from_db()
    assert s.last_digest_week == ""


def test_resubscribe_from_home_resets_to_all_and_game_adds(db, multi, game):
    s = confirmed("o@example.com", ["multi"])
    nl.subscribe("o@example.com", game="test-game")
    s.refresh_from_db()
    assert s.games == ["multi", "test-game"]
    nl.subscribe("o@example.com")  # home page: everything
    s.refresh_from_db()
    assert s.games == []


def test_subscribe_api_accepts_game(client, multi):
    r = client.post(
        "/api/v1/newsletter/subscribe/",
        {"email": "g@example.com", "game": "multi"},
        content_type="application/json",
    )
    assert r.status_code == 200 and Subscriber.objects.get(email="g@example.com").games == ["multi"]
