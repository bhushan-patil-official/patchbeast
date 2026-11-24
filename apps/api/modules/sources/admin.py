from django.contrib import admin

from modules.common.admin import AuditAdmin

from .models import Source


@admin.action(description="Fetch now (reset backoff)")
def fetch_now(modeladmin, request, queryset):
    from django.utils import timezone

    queryset.update(next_fetch_at=timezone.now(), consecutive_failures=0)


@admin.action(description="Re-enable")
def enable(modeladmin, request, queryset):
    queryset.update(enabled=True, consecutive_failures=0, failing_since=None)


@admin.register(Source)
class SourceAdmin(AuditAdmin):
    list_display = (
        "name",
        "game",
        "type",
        "enabled",
        "health",
        "consecutive_failures",
        "last_fetched",
        "is_placeholder",
    )
    list_filter = ("type", "health", "enabled", "game")
    search_fields = ("name", "url")
    actions = [fetch_now, enable]
    readonly_fields = ("etag", "last_modified", "last_fetched", "last_error", "failing_since")
