from datetime import UTC, datetime
from typing import Any

import httpx

from modules.sources import robots
from modules.sources.fetchers.rss import clean_lead
from modules.sources.http import conditional_get, make_client
from modules.sources.ports import FetchError, FetchResult, RawItem, SourceSpec


def parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC)
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    except ValueError:
        return None


def dig(obj: Any, path: str) -> Any:
    for part in filter(None, path.split(".")):
        if isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.isdigit():
            obj = obj[int(part)] if int(part) < len(obj) else None
        else:
            return None
    return obj


class JsonApiFetcher:
    """Config: items_path, title_field, url_field, date_field, lead_field, id_field, url_prefix."""

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or make_client()

    def fetch(self, spec: SourceSpec) -> FetchResult:
        if not spec.official_feed and not robots.allowed(spec.url, self.client):
            raise FetchError("blocked by robots.txt", permanent=True)
        r = conditional_get(self.client, spec.url, spec.etag, spec.last_modified, {"Accept": "application/json"})
        if r.status_code == 304:
            return FetchResult(not_modified=True, etag=spec.etag, last_modified=spec.last_modified)
        try:
            data = r.json()
        except ValueError as e:
            raise FetchError("invalid JSON") from e
        cfg = spec.config
        rows = dig(data, cfg.get("items_path", "")) if cfg.get("items_path") else data
        if not isinstance(rows, list):
            raise FetchError("items_path did not resolve to a list")
        items = []
        for row in rows[:50]:
            title = dig(row, cfg.get("title_field", "title"))
            url = dig(row, cfg.get("url_field", "url"))
            if not title or not url:
                continue
            url = f"{cfg.get('url_prefix', '')}{url}"
            items.append(
                RawItem(
                    title=clean_lead(str(title), 300), url=url,
                    published_at=parse_iso(dig(row, cfg.get("date_field", "published"))),
                    lead=clean_lead(str(dig(row, cfg["lead_field"]) or "")) if cfg.get("lead_field") else "",
                    external_id=str(dig(row, cfg.get("id_field", "id")) or url),
                )  # fmt: skip
            )
        return FetchResult(items=items, etag=r.headers.get("ETag", ""), last_modified=r.headers.get("Last-Modified", ""))
