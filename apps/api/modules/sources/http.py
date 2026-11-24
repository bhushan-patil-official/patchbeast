import httpx
from django.conf import settings

MAX_BYTES = 3 * 1024 * 1024


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": settings.PB["USER_AGENT"], "Accept": "*/*"},
        timeout=httpx.Timeout(15.0),
        follow_redirects=True,
        transport=transport,
    )


def conditional_get(client: httpx.Client, url: str, etag: str, last_modified: str, extra_headers: dict | None = None):
    from .ports import FetchError

    headers = dict(extra_headers or {})
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    try:
        r = client.get(url, headers=headers)
    except httpx.HTTPError as e:
        raise FetchError(f"network error: {e.__class__.__name__}: {e}") from e
    if r.status_code in (429, 503):
        ra = r.headers.get("Retry-After", "")
        raise FetchError(f"HTTP {r.status_code}", retry_after=int(ra) if ra.isdigit() else None)
    if r.status_code in (401, 403, 404, 410):
        raise FetchError(f"HTTP {r.status_code}", permanent=r.status_code in (404, 410))
    if r.status_code >= 400:
        raise FetchError(f"HTTP {r.status_code}")
    if len(r.content) > MAX_BYTES:
        raise FetchError("response too large")
    return r
