"""YouTube Data API adapter with a local quota ledger.

Quota costs: playlistItems.list = 1 unit, search.list = 100 units (NEVER used here).
We read the channel's *uploads playlist* (id = "UU" + channel_id[2:]) which needs no search."""

from typing import Protocol

import httpx
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from modules.sources.fetchers.json_api import parse_iso
from modules.sources.http import make_client
from modules.sources.ports import FetchError, FetchResult, RawItem, SourceSpec

PLAYLIST_ITEMS_COST = 1


class QuotaLedger(Protocol):
    def try_spend(self, units: int) -> bool: ...


class CacheQuotaLedger:
    """Daily (UTC... YouTube resets at midnight Pacific; we use UTC and keep a safety margin)."""

    def __init__(self, daily: int | None = None, margin: int | None = None):
        self.daily = daily if daily is not None else settings.PB["YOUTUBE_DAILY_QUOTA"]
        self.margin = margin if margin is not None else settings.PB["YOUTUBE_SAFETY_MARGIN"]

    def _key(self) -> str:
        return f"yt-quota:{timezone.now().date()}"

    def used(self) -> int:
        return int(cache.get(self._key(), 0))

    def try_spend(self, units: int) -> bool:
        if self.used() + units > self.daily - self.margin:
            return False
        cache.add(self._key(), 0, timeout=2 * 86400)
        cache.incr(self._key(), units)
        return True


def uploads_playlist(channel_id: str) -> str:
    if not channel_id.startswith("UC"):
        raise FetchError("config.channel_id must start with 'UC'", permanent=True)
    return "UU" + channel_id[2:]


class YouTubeFetcher:
    def __init__(self, client: httpx.Client | None = None, quota: QuotaLedger | None = None, api_key: str | None = None):
        self.client = client or make_client()
        self.quota = quota or CacheQuotaLedger()
        self.api_key = api_key if api_key is not None else settings.PB["YOUTUBE_API_KEY"]

    def fetch(self, spec: SourceSpec) -> FetchResult:
        if not self.api_key:
            raise FetchError("YOUTUBE_API_KEY not configured", permanent=True)
        playlist = uploads_playlist(spec.config.get("channel_id", ""))
        if not self.quota.try_spend(PLAYLIST_ITEMS_COST):
            raise FetchError("YouTube daily quota guard reached", retry_after=3600)
        try:
            r = self.client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={"part": "snippet,contentDetails", "playlistId": playlist, "maxResults": 25, "key": self.api_key},
            )
        except httpx.HTTPError as e:
            raise FetchError(f"network error: {e.__class__.__name__}") from e
        if r.status_code == 403:
            raise FetchError("YouTube API 403 (quota or key)", retry_after=6 * 3600)
        if r.status_code >= 400:
            raise FetchError(f"YouTube API HTTP {r.status_code}")
        items = []
        for row in r.json().get("items", []):
            sn, cd = row.get("snippet", {}), row.get("contentDetails", {})
            vid = cd.get("videoId") or sn.get("resourceId", {}).get("videoId")
            if not vid:
                continue
            items.append(
                RawItem(
                    title=sn.get("title", "")[:300], url=f"https://www.youtube.com/watch?v={vid}",
                    published_at=parse_iso(cd.get("videoPublishedAt") or sn.get("publishedAt")),
                    kind="video", external_id=vid, channel=sn.get("videoOwnerChannelTitle", sn.get("channelTitle", "")),
                )  # fmt: skip
            )
        return FetchResult(items=items)
