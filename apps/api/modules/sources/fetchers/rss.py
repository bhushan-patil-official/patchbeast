import re
from calendar import timegm
from datetime import UTC, datetime
from html import unescape

import feedparser
import httpx

from modules.sources import robots
from modules.sources.http import conditional_get, make_client
from modules.sources.ports import FetchError, FetchResult, RawItem, SourceSpec

_TAG = re.compile(r"<[^>]+>")


def clean_lead(html: str, limit: int = 600) -> str:
    return re.sub(r"\s+", " ", unescape(_TAG.sub(" ", html or ""))).strip()[:limit]


def _dt(entry) -> datetime | None:
    st = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime.fromtimestamp(timegm(st), UTC) if st else None


class RssFetcher:
    def __init__(self, client: httpx.Client | None = None):
        self.client = client or make_client()

    def fetch(self, spec: SourceSpec) -> FetchResult:
        if not spec.official_feed and not robots.allowed(spec.url, self.client):
            raise FetchError("blocked by robots.txt", permanent=True)
        r = conditional_get(self.client, spec.url, spec.etag, spec.last_modified)
        if r.status_code == 304:
            return FetchResult(not_modified=True, etag=spec.etag, last_modified=spec.last_modified)
        feed = feedparser.parse(r.content)
        if feed.bozo and not feed.entries:
            raise FetchError(f"unparseable feed: {feed.bozo_exception.__class__.__name__}")
        items = []
        for e in feed.entries[:50]:
            link, title = e.get("link"), (e.get("title") or "").strip()
            if not link or not title:
                continue
            items.append(
                RawItem(
                    title=clean_lead(title, 300), url=link, published_at=_dt(e),
                    lead=clean_lead(e.get("summary", "")), external_id=e.get("id", link),
                )  # fmt: skip
            )
        return FetchResult(
            items=items,
            etag=r.headers.get("ETag", ""),
            last_modified=r.headers.get("Last-Modified", ""),
        )
