"""URL helpers shared across modules."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "igshid", "ref", "ref_src",
    "ref_url", "source", "cmpid", "ocid", "_hsenc", "_hsmi", "yclid", "spm", "share",
}  # fmt: skip


def normalise_url(url: str) -> str:
    """Canonical form used for exact dedupe: lowercase host, no www, no fragment, no tracking
    params, sorted query, no trailing slash (except root), http(s) only."""
    url = (url or "").strip()
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise ValueError(f"not an http(s) url: {url!r}")
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = p.port
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    query = sorted(
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=False)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS
    )
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse(("https", netloc, path, "", urlencode(query), ""))


def registrable_domain(url: str) -> str:
    """Approximate eTLD+1 (no public-suffix list dependency; handles common 2-level TLDs)."""
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    if parts[-2] in {"co", "com", "org", "net", "gov", "ac"} and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])
