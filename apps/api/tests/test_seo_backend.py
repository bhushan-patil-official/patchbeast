from datetime import date, timedelta

import httpx
import pytest
from django.utils import timezone

from modules.content import services as content
from modules.content import tasks
from modules.content.models import Patch, Story
from modules.games.models import Game, Release
from modules.platform import services as platform


@pytest.fixture
def live(db):
    g = Game.objects.create(slug="live", name="Live Game", hub_config={"platforms": ["pc", "ps5"]})
    Release.objects.create(
        game=g,
        platform="ps5",
        date=date.today() - timedelta(days=2),
        confidence="confirmed",
        source_url="https://a.example.com",
    )
    return g


def patch(
    game, version, days_ago, sources=("https://a.example.com/p", "https://b.example.org/p"), **kw
):
    p = Patch.objects.create(
        game=game,
        platform="ps5",
        version=version,
        date=date.today() - timedelta(days=days_ago),
        our_summary="Our summary.",
        **kw,
    )
    for u in sources:
        content.add_evidence(game, "patch", p.pk, u)
    return p


def test_latest_patches_lists_only_real_sourced_patches_newest_first(client, live):
    patch(live, "1.0.0", 9)
    patch(live, "1.0.2", 1)
    patch(live, "1.0.1", 4)
    patch(live, "0.9", 2, sources=())  # unsourced: never promoted
    p = patch(live, "0.8", 0)
    Patch.objects.filter(pk=p.pk).update(is_placeholder=True)
    r = client.get("/api/v1/patches/latest/").json()
    assert [x["version"] for x in r] == ["1.0.2", "1.0.1", "1.0.0"]
    assert r[0]["game_slug"] == "live" and r[0]["platform"] == "ps5"


def test_latest_patches_empty_for_unindexable_game(client, live):
    patch(live, "1.0.0", 1)
    live.allow_index = False
    live.save()
    assert client.get("/api/v1/patches/latest/").json() == []


def test_sitemap_home_lastmod_is_the_newest_entry(client, live):
    patch(live, "1.0.0", 3)
    entries = client.get("/api/v1/sitemap/").json()
    home = next(e for e in entries if e["path"] == "/")
    newest = max(e["lastmod"] for e in entries if e["lastmod"])
    assert home["lastmod"] == newest and home["lastmod"] is not None


def test_story_card_exposes_updated_at(client, live):
    Story.objects.create(
        game=live,
        slug="s",
        title="A briefing title here",
        status="published",
        published_at=timezone.now(),
        blocks=[{"text": "t", "sources": [0, 1]}],
        sources=[
            {"article_id": 1, "url": "https://a.example.com", "name": "a", "title": "t"},
            {"article_id": 2, "url": "https://b.example.org", "name": "b", "title": "t"},
        ],
        cluster_key="k",
    )
    assert client.get("/api/v1/stories/").json()["results"][0]["updated_at"]


# ---------- IndexNow ----------
def set_pb(settings, **kw):
    settings.PB = {**settings.PB, **kw}


def test_indexnow_noop_without_key_or_on_localhost(settings):
    called = []
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: called.append(r) or httpx.Response(200))
    )
    set_pb(settings, INDEXNOW_KEY="")
    settings.SITE_URL = "https://patchbeast.com"
    assert platform.post_indexnow(["https://patchbeast.com/a"], client) is False
    set_pb(settings, INDEXNOW_KEY="abc12345")
    settings.SITE_URL = "http://localhost:3000"
    assert platform.post_indexnow(["http://localhost:3000/a"], client) is False
    assert called == []


def test_indexnow_payload(settings):
    seen = {}

    def handler(req: httpx.Request):
        import json

        seen.update(json.loads(req.content), url=str(req.url))
        return httpx.Response(200)

    set_pb(settings, INDEXNOW_KEY="abc12345")
    settings.SITE_URL = "https://patchbeast.com"
    assert (
        platform.post_indexnow(
            ["https://patchbeast.com/news"], httpx.Client(transport=httpx.MockTransport(handler))
        )
        is True
    )
    assert seen == {"host": "patchbeast.com", "key": "abc12345", "keyLocation": "https://patchbeast.com/indexnow.txt",
                    "urlList": ["https://patchbeast.com/news"], "url": "https://api.indexnow.org/indexnow"}  # fmt: skip


def test_task_submits_only_indexable_paths_once(settings, live, monkeypatch):
    patch(live, "1.0.0", 1)
    set_pb(settings, INDEXNOW_KEY="abc12345")
    settings.SITE_URL = "https://patchbeast.com"
    sent = []
    monkeypatch.setattr(tasks, "post_indexnow", lambda urls, client=None: sent.append(urls) or True)
    paths = [
        "/",
        "/news",
        "/games/live/patches/ps5/1.0.0",
        "/feed",
        "/games/live/videos",
        "/admin/",
    ]
    assert tasks.submit_indexnow(paths) == 2
    assert sent[0] == [
        "https://patchbeast.com/news",
        "https://patchbeast.com/games/live/patches/ps5/1.0.0",
    ]  # no /feed, no empty section
    assert tasks.submit_indexnow(paths) == 0  # debounced for 10 minutes


def test_saving_a_patch_schedules_indexnow_for_its_page(
    settings, live, monkeypatch, django_capture_on_commit_callbacks
):
    set_pb(settings, INDEXNOW_KEY="abc12345")
    calls = []
    monkeypatch.setattr(tasks.submit_indexnow, "delay", lambda paths: calls.append(paths))
    with django_capture_on_commit_callbacks(execute=True):
        Patch.objects.create(game=live, platform="ps5", version="2.0", our_summary="s")
    assert calls and "/games/live/patches/ps5/2.0" in calls[0] and "/news" in calls[0]


def test_no_indexnow_scheduling_without_a_key(
    settings, live, monkeypatch, django_capture_on_commit_callbacks
):
    set_pb(settings, INDEXNOW_KEY="")
    calls = []
    monkeypatch.setattr(tasks.submit_indexnow, "delay", lambda paths: calls.append(paths))
    with django_capture_on_commit_callbacks(execute=True):
        Patch.objects.create(game=live, platform="ps5", version="3.0", our_summary="s")
    assert calls == []
