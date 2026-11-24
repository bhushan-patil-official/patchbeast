from django.contrib import admin
from django.utils.html import format_html

from modules.common.admin import AuditAdmin

from . import services
from .models import Article, Change, Evidence, Patch, Requirement, Video


@admin.register(Article)
class ArticleAdmin(AuditAdmin):
    list_display = (
        "title",
        "game",
        "status",
        "verification",
        "confidence",
        "source_name",
        "created_at",
    )
    list_filter = ("status", "game", "verification")
    search_fields = ("title", "source_url")
    readonly_fields = ("simhash", "canonical_url")


@admin.register(Patch)
class PatchAdmin(AuditAdmin):
    list_display = ("game", "version", "date", "verification", "source_count", "is_placeholder")
    list_filter = ("game", "verification")


@admin.register(Requirement)
class RequirementAdmin(AuditAdmin):
    list_display = (
        "game",
        "platform",
        "tier",
        "cpu",
        "gpu",
        "ram_gb",
        "verification",
        "is_placeholder",
    )
    list_filter = ("game", "tier", "verification")


@admin.action(description="Publish selected videos")
def publish_videos(modeladmin, request, queryset):
    for v in queryset.filter(status=Video.Status.QUEUED):
        services.approve_video(v, request.user)


@admin.register(Video)
class VideoAdmin(AuditAdmin):
    list_display = ("title", "game", "channel", "kind", "status", "published_at", "watch")
    list_filter = ("status", "game", "kind")
    actions = [publish_videos]

    @admin.display(description="link")
    def watch(self, obj):
        return format_html(
            '<a href="https://www.youtube.com/watch?v={}" target="_blank" rel="noopener">open</a>',
            obj.youtube_id,
        )


@admin.action(description="Recompute verification for selected evidence subjects")
def recompute(modeladmin, request, queryset):
    for ev in queryset:
        services.recompute_verification(ev.subject_kind, ev.subject_id)


@admin.register(Evidence)
class EvidenceAdmin(AuditAdmin):
    list_display = ("game", "subject_kind", "subject_id", "domain", "kind", "created_at")
    list_filter = ("subject_kind", "kind", "game")
    actions = [recompute]

    def save_model(self, request, obj, form, change):
        from modules.common.urlutils import registrable_domain

        obj.domain = registrable_domain(obj.url)
        super().save_model(request, obj, form, change)
        services.recompute_verification(obj.subject_kind, obj.subject_id)


@admin.register(Change)
class ChangeAdmin(AuditAdmin):
    list_display = ("occurred_at", "game", "kind", "title", "verification", "is_public")
    list_filter = ("kind", "game", "is_public")
