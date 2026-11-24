"""Anthropic adapter with retry/backoff. No sampling params are sent (Haiku 5.5 rejects
non-default values); effort=low keeps classification cheap and fast."""

import logging
import random
import time

import anthropic

from .ports import LLMRefused, LLMResponse, LLMRetryable

log = logging.getLogger(__name__)


class AnthropicClient:
    def __init__(self, api_key: str, model: str, *, max_attempts: int = 3, sleep=time.sleep, client=None):
        # SDK retries disabled: we own the retry policy so spend accounting stays accurate.
        self._c = client or anthropic.Anthropic(api_key=api_key, max_retries=0, timeout=45.0)
        self.model = model
        self.max_attempts = max_attempts
        self._sleep = sleep

    def complete(self, system: str, user: str, max_tokens: int = 700) -> LLMResponse:
        last: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                msg = self._c.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    output_config={"effort": "low"},
                )
                if msg.stop_reason == "refusal":
                    raise LLMRefused("provider refused the request")
                text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
                return LLMResponse(
                    text=text, input_tokens=msg.usage.input_tokens, output_tokens=msg.usage.output_tokens,
                    model=self.model, stop_reason=msg.stop_reason or "end_turn",
                )  # fmt: skip
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError) as e:
                last = e
            except anthropic.APIStatusError as e:
                if e.status_code in (408, 409, 429, 529) or e.status_code >= 500:
                    last = e
                else:
                    raise LLMRetryable(f"non-retryable API error {e.status_code}") from e
            delay = min(30.0, 2.0 * (2**attempt)) * (0.5 + random.random())
            log.warning("llm retry %s/%s in %.1fs: %s", attempt + 1, self.max_attempts, delay, last.__class__.__name__)
            self._sleep(delay)
        raise LLMRetryable(f"LLM unavailable after {self.max_attempts} attempts: {last.__class__.__name__}")
