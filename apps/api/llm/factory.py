from django.conf import settings

from .fake import FakeLLMClient
from .ports import LLMClient, LLMUnavailable


class NullClient:
    model = "none"

    def complete(self, system, user, max_tokens=700):
        raise LLMUnavailable("no LLM provider configured (set ANTHROPIC_API_KEY)")


def get_llm_client() -> LLMClient:
    provider = settings.PB["LLM_PROVIDER"]
    if provider == "fake":
        return FakeLLMClient()
    if provider == "anthropic" and settings.PB["ANTHROPIC_API_KEY"]:
        from .anthropic_client import AnthropicClient

        return AnthropicClient(settings.PB["ANTHROPIC_API_KEY"], settings.PB["LLM_MODEL"])
    return NullClient()
