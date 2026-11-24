"""Provider-agnostic LLM port."""

from dataclasses import dataclass
from typing import Protocol


class LLMError(Exception):
    pass


class LLMRetryable(LLMError):
    """Transient provider problem (rate limit, overload, network)."""


class LLMRefused(LLMError):
    """Provider declined the request (safety stop)."""


class LLMUnavailable(LLMError):
    """No provider configured / kill switch / spend cap."""


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    stop_reason: str = "end_turn"


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str, max_tokens: int = 700) -> LLMResponse: ...
