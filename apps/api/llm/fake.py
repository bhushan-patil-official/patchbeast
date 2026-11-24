"""Deterministic adapter for tests and keyless dev."""

from collections.abc import Callable

from .ports import LLMResponse


class FakeLLMClient:
    model = "fake-model"

    def __init__(self, responses: list[str | Exception] | Callable[[str, str], str] | None = None):
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, max_tokens: int = 700) -> LLMResponse:
        self.calls.append((system, user))
        r = self.responses
        if callable(r):
            text = r(system, user)
        elif isinstance(r, list) and r:
            item = r.pop(0)
            if isinstance(item, Exception):
                raise item
            text = item
        else:
            text = "{}"
        return LLMResponse(text=text, input_tokens=len(system + user) // 4, output_tokens=len(text) // 4, model=self.model)
