"""robots.txt check (cached 24h). Fail-open on network errors, fail-closed on explicit disallow."""

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from django.conf import settings
from django.core.cache import cache


def allowed(url: str, client: httpx.Client) -> bool:
    p = urlparse(url)
    origin = f"{p.scheme}://{p.netloc}"
    key = f"robots:{origin}"
    body = cache.get(key)
    if body is None:
        try:
            r = client.get(f"{origin}/robots.txt", timeout=10)
            body = r.text if r.status_code == 200 else ""
        except httpx.HTTPError:
            body = ""
        cache.set(key, body, 24 * 3600)
    if not body:
        return True
    rp = RobotFileParser()
    rp.parse(body.splitlines())
    return rp.can_fetch(settings.PB["USER_AGENT"], url) or rp.can_fetch("*", url)
