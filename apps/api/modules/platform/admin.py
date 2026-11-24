from django.contrib import admin

from modules.common.admin import AuditAdmin

from .models import AlertEvent, FeatureFlag, LLMUsage, SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(AuditAdmin):
    list_display = ("__str__", "kill_switch", "auto_publish_enabled", "daily_llm_cap", "daily_llm_spend", "spend_date")
    fields = ("kill_switch", "auto_publish_enabled", "daily_llm_cap", "daily_llm_spend", "spend_date")

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FeatureFlag)
class FeatureFlagAdmin(AuditAdmin):
    list_display = ("key", "enabled", "note")
    list_editable = ("enabled",)


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "delivered_via", "message")
    list_filter = ("kind",)
    readonly_fields = [f.name for f in AlertEvent._meta.fields]


@admin.register(LLMUsage)
class LLMUsageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "model", "purpose", "input_tokens", "output_tokens", "cost_usd", "ok")
    list_filter = ("day", "ok")
