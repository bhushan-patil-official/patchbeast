from decimal import Decimal

from django.db import models

from modules.common.models import AuditModel


class SiteSetting(AuditModel):
    """Singleton (pk=1): kill switch + LLM spend cap/ledger."""

    kill_switch = models.BooleanField(
        default=False,
        help_text="ON = pause fetching, LLM calls and auto-publishing. Read API keeps serving.",
    )
    daily_llm_cap = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal("1.0000"))
    daily_llm_spend = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal("0"))
    spend_date = models.DateField(null=True, blank=True)
    auto_publish_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "site setting"

    def __str__(self) -> str:
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSetting":
        from django.conf import settings

        obj, _ = cls.objects.get_or_create(
            pk=1, defaults={"daily_llm_cap": Decimal(str(settings.PB["LLM_DAILY_CAP_USD"]))}
        )
        return obj


class FeatureFlag(AuditModel):
    key = models.SlugField(unique=True)
    enabled = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f"{self.key}={'on' if self.enabled else 'off'}"


class AlertEvent(AuditModel):
    kind = models.CharField(max_length=60, db_index=True)
    message = models.TextField()
    dedupe_key = models.CharField(max_length=200, blank=True)
    delivered_via = models.CharField(max_length=100, blank=True)
    suppressed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]


class LLMUsage(AuditModel):
    day = models.DateField(db_index=True)
    model = models.CharField(max_length=80)
    purpose = models.CharField(max_length=40, default="classify")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal("0"))
    ok = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
