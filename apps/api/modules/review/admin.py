from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_POST

from . import services
from .models import QueuedArticle, ReviewAction


@admin.register(QueuedArticle)
class ReviewQueueAdmin(admin.ModelAdmin):
    """Custom view: one card per item, approve/reject/edit in one click, keyboard friendly (j/k/a/r/e/?)."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        v = self.admin_site.admin_view
        return [
            path("act/<int:pk>/", v(require_POST(self.act)), name="review_act"),
            path("video/<int:pk>/", v(require_POST(self.video_act)), name="review_video_act"),
            *super().get_urls(),
        ]

    def changelist_view(self, request: HttpRequest, extra_context=None):
        ctx = {
            **self.admin_site.each_context(request),
            "title": "Review queue",
            "opts": self.model._meta,
            "items": services.queue(),
            "videos": services.video_queue(),
            "act_url": "admin:review_act",
        }
        return TemplateResponse(request, "review/queue.html", ctx)

    def act(self, request: HttpRequest, pk: int):
        action = request.POST.get("action")
        try:
            if action == "approve":
                services.approve(
                    pk,
                    request.user,
                    title=request.POST.get("title"),
                    summary=request.POST.get("summary"),
                    tags=request.POST.get("tags"),
                )
                messages.success(request, "Approved and published.")
            elif action == "reject":
                services.reject(pk, request.user, request.POST.get("reason", ""))
                messages.info(request, "Rejected.")
            elif action == "save":
                services.save_edit(
                    pk,
                    request.user,
                    title=request.POST["title"],
                    summary=request.POST["summary"],
                    tags=request.POST.get("tags", ""),
                )
                messages.success(request, "Saved.")
        except ValueError as e:
            messages.error(request, str(e))
        return HttpResponseRedirect(reverse("admin:review_queuedarticle_changelist"))

    def video_act(self, request: HttpRequest, pk: int):
        services.video_decision(pk, request.user, request.POST.get("action") == "approve")
        return HttpResponseRedirect(reverse("admin:review_queuedarticle_changelist"))


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "article", "action", "created_by")
    list_filter = ("action",)
