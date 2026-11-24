"""WebSub (PubSubHubbub) adapter for YouTube push notifications.

Polling is a no-op (push-driven). The receiver endpoint (api/hook_views.py) uses
`verify_signature` + `parse_notification`; `subscribe` registers with the hub."""

import hashlib
import hmac
from datetime import datetime

import defusedxml.ElementTree as ET
import httpx

from modules.sources.fetchers.json_api import parse_iso
from modules.sources.http import make_client
from modules.sources.ports import FetchResult, RawItem, SourceSpec

HUB = "https://pubsubhubbub.appspot.com/subscribe"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


class WebSubFetcher:
    def fetch(self, spec: SourceSpec) -> FetchResult:
        return FetchResult(not_modified=True)


def topic_url(channel_id: str) -> str:
    return f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"


def subscribe(
    channel_id: str,
    callback: str,
    secret: str,
    client: httpx.Client | None = None,
    lease: int = 432000,
) -> None:
    c = client or make_client()
    r = c.post(
        HUB,
        data={
            "hub.mode": "subscribe", "hub.topic": topic_url(channel_id), "hub.callback": callback,
            "hub.verify": "async", "hub.secret": secret, "hub.lease_seconds": str(lease),
        },
    )  # fmt: skip
    r.raise_for_status()


def verify_signature(body: bytes, header: str, secret: str) -> bool:
    if not header or "=" not in header:
        return False
    algo, _, sig = header.partition("=")
    if algo not in ("sha1", "sha256", "sha512"):
        return False
    digest = hmac.new(secret.encode(), body, getattr(hashlib, algo)).hexdigest()
    return hmac.compare_digest(digest, sig)


def parse_notification(body: bytes) -> list[RawItem]:
    root = ET.fromstring(body)
    out = []
    for e in root.findall("a:entry", NS):
        vid = (e.findtext("yt:videoId", namespaces=NS) or "").strip()
        title = (e.findtext("a:title", namespaces=NS) or "").strip()
        if not vid or not title:
            continue
        published: datetime | None = parse_iso(e.findtext("a:published", namespaces=NS))
        out.append(
            RawItem(
                title=title[:300], url=f"https://www.youtube.com/watch?v={vid}", published_at=published,
                kind="video", external_id=vid, channel=(e.findtext("a:author/a:name", namespaces=NS) or ""),
            )  # fmt: skip
        )
    return out
