import httpx
import pytest

from modules.sources import services as source_services
from modules.sources.fetchers.json_api import JsonApiFetcher
from modules.sources.fetchers.rss import RssFetcher
from modules.sources.fetchers.websub import parse_notification, verify_signature
from modules.sources.fetchers.youtube import CacheQuotaLedger, YouTubeFetcher, uploads_playlist
from modules.sources.ports import FetchError, SourceSpec

from .conftest import make_client


def spec(**kw):
    base = {
        "id": 1,
        "type": "rss",
        "url": "https://news.example.com/feed.xml",
        "official_feed": True,
    }
    base.update(kw)
    return SourceSpec(**base)


def test_rss_parses_fixture_and_skips_broken_items(fixture_text):
    seen = {}

    def handler(req: httpx.Request):
        seen["inm"] = req.headers.get("If-None-Match")
        return httpx.Response(
            200,
            text=fixture_text("newsroom.xml"),
            headers={"ETag": '"v1"', "Last-Modified": "Mon, 02 Nov 2026 10:00:00 GMT"},
        )

    res = RssFetcher(make_client(handler)).fetch(spec())
    assert [i.title for i in res.items] == ["Patch 1.02 now live", "Release date announced for PC"]
    assert res.items[0].lead.startswith("Version 1.02 is rolling out")  # html stripped
    assert "<p>" not in res.items[0].lead
    assert res.etag == '"v1"' and res.last_modified
    assert res.items[0].published_at.year == 2026


def test_rss_conditional_get_sends_validators_and_handles_304():
    def handler(req: httpx.Request):
        assert req.headers["If-None-Match"] == '"v1"'
        assert req.headers["If-Modified-Since"] == "Mon, 02 Nov 2026 10:00:00 GMT"
        return httpx.Response(304)

    res = RssFetcher(make_client(handler)).fetch(
        spec(etag='"v1"', last_modified="Mon, 02 Nov 2026 10:00:00 GMT")
    )
    assert res.not_modified and res.items == []


def test_rss_respects_robots_disallow(db):
    def handler(req: httpx.Request):
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /feed.xml\n")
        raise AssertionError("feed must not be fetched")

    with pytest.raises(FetchError) as e:
        RssFetcher(make_client(handler)).fetch(spec(official_feed=False))
    assert e.value.permanent


@pytest.mark.parametrize(
    "status,permanent,retry", [(404, True, None), (429, False, 120), (500, False, None)]
)
def test_http_errors_map_to_fetch_error(status, permanent, retry):
    headers = {"Retry-After": "120"} if status == 429 else {}
    with pytest.raises(FetchError) as e:
        RssFetcher(make_client(lambda r: httpx.Response(status, headers=headers))).fetch(spec())
    assert e.value.permanent is permanent and e.value.retry_after == retry


def test_rss_garbage_is_an_error():
    with pytest.raises(FetchError):
        RssFetcher(make_client(lambda r: httpx.Response(200, text="<html>nope"))).fetch(spec())


def test_json_api_fetcher_maps_config(fixture_text):
    cfg = {
        "items_path": "data.items",
        "title_field": "headline",
        "url_field": "path",
        "url_prefix": "https://x.example.com",
        "date_field": "published",
        "lead_field": "blurb",
    }
    res = JsonApiFetcher(
        make_client(lambda r: httpx.Response(200, text=fixture_text("api_news.json")))
    ).fetch(spec(type="api", url="https://x.example.com/api", config=cfg))
    assert len(res.items) == 1
    assert (
        res.items[0].url == "https://x.example.com/n/hotfix-103"
        and res.items[0].published_at.day == 4
    )


def test_youtube_uses_playlist_items_never_search(db, fixture_text):
    urls = []

    def handler(req: httpx.Request):
        urls.append(str(req.url))
        return httpx.Response(200, text=fixture_text("youtube_playlist.json"))

    ledger = CacheQuotaLedger(daily=10000, margin=500)
    f = YouTubeFetcher(make_client(handler), ledger, api_key="k")
    res = f.fetch(spec(type="youtube", url="", config={"channel_id": "UCabcdefghijklmnopqrstuv"}))
    assert all("playlistItems" in u and "search" not in u for u in urls)
    assert "playlistId=UUabcdefghijklmnopqrstuv" in urls[0]
    assert [v.external_id for v in res.items] == ["abc123XYZ_-", "def456"] and res.items[
        0
    ].kind == "video"
    assert ledger.used() == 1


def test_youtube_quota_guard_stops_calls(db):
    ledger = CacheQuotaLedger(daily=10, margin=5)
    f = YouTubeFetcher(
        make_client(lambda r: httpx.Response(200, json={"items": []})), ledger, api_key="k"
    )
    s = spec(type="youtube", url="", config={"channel_id": "UCabcdefghijklmnopqrstuv"})
    for _ in range(5):
        f.fetch(s)
    with pytest.raises(FetchError) as e:
        f.fetch(s)
    assert "quota" in str(e.value) and e.value.retry_after


def test_youtube_bad_channel_id():
    with pytest.raises(FetchError):
        uploads_playlist("nope")


def test_websub_signature_and_parse(fixture_text):
    import hashlib
    import hmac

    body = fixture_text("websub_push.xml").encode()
    sig = "sha1=" + hmac.new(b"s3cret", body, hashlib.sha1).hexdigest()
    assert verify_signature(body, sig, "s3cret")
    assert not verify_signature(body, sig, "other")
    assert not verify_signature(body, "", "s3cret")
    items = parse_notification(body)
    assert items[0].external_id == "push12345" and items[0].kind == "video"


def test_failure_backoff_and_health(source):
    for _ in range(3):
        source_services.mark_failure(source, "HTTP 500")
    source.refresh_from_db()
    assert source.health == "failing" and source.consecutive_failures == 3 and source.enabled
    assert (
        source_services.backoff_minutes(1, 10) == 10
        and source_services.backoff_minutes(4, 10) == 80
    )
    assert source_services.backoff_minutes(20, 10) == 360  # capped


def test_permanent_failure_disables_source_and_alerts(source, mailoutbox):
    source_services.mark_failure(source, "HTTP 404", permanent=True)
    source_services.mark_failure(source, "HTTP 404", permanent=True)
    source.refresh_from_db()
    assert not source.enabled
    assert any("AUTO-DISABLED" in m.body for m in mailoutbox)
