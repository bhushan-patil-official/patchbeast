from django.contrib import admin

from .models import FetchLog


@admin.register(FetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "source", "ok", "not_modified", "items_seen", "items_new", "duration_ms", "error")
    list_filter = ("ok", "source")
    readonly_fields = [f.name for f in FetchLog._meta.fields]

    def has_add_permission(self, request):
        return False
