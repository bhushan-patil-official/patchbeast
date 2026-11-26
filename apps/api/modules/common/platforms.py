"""Platform registry. PC-first: PC is always listed first. Adding a platform = one line here."""

PLATFORMS: dict[str, str] = {
    "pc": "PC",
    "ps5": "PlayStation 5",
    "xbox_series": "Xbox Series X|S",
    "switch2": "Nintendo Switch 2",
}
SHORT_LABELS = {"pc": "PC", "ps5": "PS5", "xbox_series": "Xbox", "switch2": "Switch 2"}

_ALIASES = {
    "pc": "pc", "windows": "pc", "steam": "pc", "epic": "pc", "epic games store": "pc",
    "ps5": "ps5", "playstation 5": "ps5", "playstation5": "ps5", "ps 5": "ps5", "playstation": "ps5",
    "xbox": "xbox_series", "xbox series x": "xbox_series", "xbox series s": "xbox_series",
    "xbox series x|s": "xbox_series", "xbox series": "xbox_series", "xbox_series": "xbox_series",
    "switch 2": "switch2", "switch2": "switch2", "nintendo switch 2": "switch2",
}  # fmt: skip


def normalise_platform(value: str | None) -> str:
    """Map free text to a registry id; unknown values become 'other' (never auto-published)."""
    key = (value or "").strip().lower()
    return _ALIASES.get(key, key if key in PLATFORMS else "other")


def label(platform: str) -> str:
    return PLATFORMS.get(platform, platform)


def short_label(platform: str) -> str:
    return SHORT_LABELS.get(platform, platform)


RESERVED_PATHS = {
    "games", "news", "feed", "about", "privacy", "terms", "contact", "affiliate-disclosure",
    "newsletter", "internal", "api", "admin", "static", "sitemap.xml", "robots.txt", "icon.svg",
    "opengraph-image", "healthz", "metrics", "hooks", "_next", "og", "rss.xml", "indexnow.txt",
    "editorial-policy", "favicon.ico", "manifest.webmanifest",
}  # fmt: skip
