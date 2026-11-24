from django.contrib import admin, messages
from django.utils.html import format_html

from modules.common.admin import AuditAdmin

from . import services
from .models import Article, Change, Evidence, Patch, Requirement, Story, Video


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
    actions = ["publish_selected", "reject_selected"]

    def save_model(self, request, obj, form, change):
        """Publishing/rejecting from this form runs the SAME logic as the review queue
        (sources, verification, published date, timeline entry, site refresh)."""
        old = form.initial.get("status") if change else None
        new = obj.status
        if change and "status" in form.changed_data:
            if new == Article.Status.PUBLISHED and old != Article.Status.PUBLISHED:
                obj.status = old
                super().save_model(request, obj, form, change)
                try:
                    services.approve_article(obj, request.user)
                    messages.success(request, "Published. The website refreshes within seconds.")
                except ValueError as e:
                    messages.error(request, f"Not published: {e}. It stays '{old}'.")
                return
            if new == Article.Status.REJECTED and old == Article.Status.PUBLISHED:
                obj.status = old
                super().save_model(request, obj, form, change)
                services.reject_article(obj, request.user, obj.review_reason)
                messages.info(request, "Rejected and removed from the site.")
                return
            if old == Article.Status.PUBLISHED:  # un-publish back to queued/new
                Change.objects.filter(subject_kind="article", subject_id=obj.pk).update(
                    is_public=False
                )
        super().save_model(request, obj, form, change)

    @admin.action(description="Publish selected (needs a game and our summary)")
    def publish_selected(self, request, queryset):
        ok = 0
        for a in queryset.exclude(status=Article.Status.PUBLISHED):
            try:
                services.approve_article(a, request.user)
                ok += 1
            except ValueError as e:
                messages.warning(request, f"#{a.pk} not published: {e}")
        messages.success(request, f"Published {ok} article(s).")

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        n = 0
        for a in queryset.exclude(status=Article.Status.REJECTED):
            services.reject_article(a, request.user, "rejected in admin")
            n += 1
        messages.info(request, f"Rejected {n} article(s).")


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


@admin.register(Story)
class StoryAdmin(AuditAdmin):
    list_display = ("title", "game", "status", "verification", "published_at", "created_at")
    list_filter = ("status", "game")
    search_fields = ("title",)
    readonly_fields = ("cluster_key", "model", "sources", "verification")
