from datetime import date, timedelta

from django.utils import timezone

from modules.content.models import Article, Patch, Requirement, Video
from modules.games.models import Release


def test_placeholder_game_is_noindex_and_countdown_frozen(client, game):
    Release.objects.create(game=game, date=None, confidence="rumour", is_placeholder=True)
    h = client.get("/api/v1/games/test-game/").json()
    assert h["seo"]["indexable"] is False and h["release"]["countdown_mode"] == "unconfirmed"
    assert client.get("/api/v1/sitemap/").json() == [{"path": "/", "lastmod": None}]


def test_rumour_date_never_counts_down(client, game):
    Release.objects.create(game=game, date=date.today() + timedelta(days=30), confidence="rumour")
    h = client.get("/api/v1/games/test-game/").json()
    assert h["release"]["countdown_mode"] == "unconfirmed" and h["seo"]["indexable"] is False


def test_real_content_makes_page_indexable_and_enters_sitemap(client, game):
    Release.objects.create(
        game=game,
        date=date.today() + timedelta(days=30),
        confidence="reported",
        source_url="https://a.example.com",
    )
    Patch.objects.create(game=game, version="1.0", date=date.today())
    h = client.get("/api/v1/games/test-game/").json()
    assert h["release"]["countdown_mode"] == "live" and h["seo"]["indexable"] is True
    paths = {e["path"] for e in client.get("/api/v1/sitemap/").json()}
    assert {"/games/test-game", "/games/test-game/patches"} <= paths
    assert "/games/test-game/videos" not in paths  # no real videos yet
    assert client.get("/api/v1/games/test-game/videos/").json()["seo"]["indexable"] is False


def test_allow_index_false_forces_noindex(client, game):
    Patch.objects.create(game=game, version="1.0")
    game.allow_index = False
    game.save()
    assert client.get("/api/v1/games/test-game/").json()["seo"]["indexable"] is False


def test_news_is_curated_only_feed_has_unreviewed(client, game):
    mk = lambda i, st: Article.objects.create(
        game=game,
        title=f"t{i}",
        source_url=f"https://x.example.com/{i}",
        canonical_url=f"https://x.example.com/{i}",
        status=st,
        our_summary="s",
        published_at=timezone.now() if st == "published" else None,
    )
    mk(1, "published")
    mk(2, "queued")
    mk(3, "rejected")
    mk(4, "new")
    news = client.get("/api/v1/news/").json()
    assert [a["title"] for a in news["results"]] == ["t1"]
    assert {a["title"] for a in client.get("/api/v1/feed/").json()["results"]} == {"t1", "t2", "t4"}
    assert {"title", "source_url", "our_summary", "tags", "verification"} <= set(news["results"][0])


def test_unpublished_videos_hidden_and_404(client, game):
    Video.objects.create(game=game, youtube_id="q1", title="queued", status="queued")
    Video.objects.create(game=game, youtube_id="p1", title="pub", status="published")
    assert [
        v["youtube_id"] for v in client.get("/api/v1/games/test-game/videos/").json()["items"]
    ] == ["p1"]
    assert client.get("/api/v1/games/nope/").status_code == 404


def test_ticker_only_confirmed(client, game):
    from modules.content import services as c

    c.record_change(game, "patch", "reported one", verification="reported")
    c.record_change(game, "patch", "confirmed one", verification="confirmed")
    assert [t["title"] for t in client.get("/api/v1/ticker/").json()] == ["confirmed one"]


def test_disabled_game_not_served(client, game):
    game.enabled = False
    game.save()
    assert client.get("/api/v1/games/test-game/").status_code == 404


def test_requirements_endpoint_and_config(client, game):
    Requirement.objects.create(game=game, tier="min", cpu="i5", gpu="gtx", ram_gb=8)
    r = client.get("/api/v1/games/test-game/requirements/").json()
    assert r["items"][0]["tier"] == "min" and r["seo"]["indexable"] is True
    c = client.get("/api/v1/config/").json()
    assert c["flags"]["ads"] is False and c["flags"]["affiliate"] is False
