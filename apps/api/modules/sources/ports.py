"""SourceFetcher port. Adapters know nothing about Django models: they receive a SourceSpec."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class FetchError(Exception):
    def __init__(self, message: str, *, retry_after: int | None = None, permanent: bool = False):
        super().__init__(message)
        self.retry_after = retry_after
        self.permanent = permanent


@dataclass(frozen=True)
class SourceSpec:
    id: int
    type: str
    url: str
    etag: str = ""
    last_modified: str = ""
    config: dict = field(default_factory=dict)
    official_feed: bool = False
    name: str = ""


@dataclass
class RawItem:
    """What a fetcher yields. `lead` is transient: fed to the LLM, never stored."""

    title: str
    url: str
    published_at: datetime | None = None
    lead: str = ""
    kind: str = "article"  # article | video
    external_id: str = ""
    channel: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class FetchResult:
    items: list[RawItem] = field(default_factory=list)
    not_modified: bool = False
    etag: str = ""
    last_modified: str = ""


class SourceFetcher(Protocol):
    def fetch(self, spec: SourceSpec) -> FetchResult: ...
