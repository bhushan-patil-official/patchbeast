from django.contrib import admin

from modules.common.admin import AuditAdmin

from .models import Game, Release


class ReleaseInline(admin.TabularInline):
    model = Release
    extra = 0
    fields = (
        "platform",
        "date",
        "confidence",
        "source_url",
        "is_current",
        "is_placeholder",
        "note",
    )


@admin.register(Game)
class GameAdmin(AuditAdmin):
    list_display = (
        "name",
        "slug",
        "vanity_path",
        "enabled",
        "is_placeholder",
        "allow_index",
        "sort_order",
    )
    list_filter = ("enabled", "is_placeholder")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ReleaseInline]


@admin.register(Release)
class ReleaseAdmin(AuditAdmin):
    list_display = (
        "game",
        "platform",
        "date",
        "confidence",
        "is_current",
        "is_placeholder",
        "created_at",
    )
    list_filter = ("confidence", "is_current", "game")
