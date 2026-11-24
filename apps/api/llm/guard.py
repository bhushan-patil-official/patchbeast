"""SpendGuard: kill switch + daily spend cap + usage accounting around any LLMClient."""

from decimal import Decimal

from django.conf import settings

from modules.platform import services as platform

from .ports import LLMClient, LLMError, LLMResponse, LLMUnavailable


def cost_usd(tokens_in: int, tokens_out: int) -> Decimal:
    return (
        Decimal(str(settings.PB["LLM_PRICE_IN"])) * tokens_in + Decimal(str(settings.PB["LLM_PRICE_OUT"])) * tokens_out
    ) / Decimal(1_000_000)


class SpendGuard:
    def __init__(self, inner: LLMClient, purpose: str = "classify"):
        self.inner = inner
        self.purpose = purpose
        self.model = inner.model

    def complete(self, system: str, user: str, max_tokens: int = 700) -> LLMResponse:
        if platform.kill_switch_on():
            raise LLMUnavailable("kill switch is ON")
        est_in = (len(system) + len(user)) // 3 + 50
        reserved = cost_usd(est_in, max_tokens)
        try:
            platform.reserve_spend(reserved)
        except platform.SpendCapExceeded as e:
            raise LLMUnavailable(str(e)) from e
        try:
            resp = self.inner.complete(system, user, max_tokens)
        except LLMError:
            platform.settle_spend(reserved, Decimal("0"), model=self.model, tokens_in=0, tokens_out=0, purpose=self.purpose, ok=False)
            raise
        actual = cost_usd(resp.input_tokens, resp.output_tokens)
        platform.settle_spend(
            reserved, actual, model=resp.model, tokens_in=resp.input_tokens, tokens_out=resp.output_tokens, purpose=self.purpose
        )
        return resp
