"""Adapter registry: adding a source type = one class + one line here."""

from collections.abc import Callable

from .fetchers.json_api import JsonApiFetcher
from .fetchers.rss import RssFetcher
from .fetchers.websub import WebSubFetcher
from .fetchers.youtube import YouTubeFetcher
from .ports import SourceFetcher

REGISTRY: dict[str, Callable[[], SourceFetcher]] = {
    "rss": RssFetcher,
    "api": JsonApiFetcher,
    "youtube": YouTubeFetcher,
    "websub": WebSubFetcher,
}


def get_fetcher(type_: str) -> SourceFetcher:
    try:
        return REGISTRY[type_]()
    except KeyError:
        raise ValueError(f"no fetcher registered for source type {type_!r}") from None
