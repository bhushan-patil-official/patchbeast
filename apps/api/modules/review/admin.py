from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_POST

from modules.games.models import Game

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
            path("bulk/", v(require_POST(self.bulk_act)), name="review_bulk"),
            path("video/<int:pk>/", v(require_POST(self.video_act)), name="review_video_act"),
            path("story/<int:pk>/", v(require_POST(self.story_act)), name="review_story_act"),
            *super().get_urls(),
        ]

    def _back(self, request: HttpRequest) -> HttpResponseRedirect:
        url = reverse("admin:review_queuedarticle_changelist")
        game = request.POST.get("return_game") or ""
        return HttpResponseRedirect(f"{url}?game={game}" if game else url)

    def bulk_act(self, request: HttpRequest):
        ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit()]
        for line in services.bulk(
            request.POST.get("action", ""), ids, request.user, request.POST.get("reason", "")
        ):
            messages.info(request, line)
        return self._back(request)

    def changelist_view(self, request: HttpRequest, extra_context=None):
        current = request.GET.get("game", "")
        ctx = {
            **self.admin_site.each_context(request),
            "title": "Review queue",
            "opts": self.model._meta,
            "items": services.queue(game=current or None),
            "games": Game.objects.filter(enabled=True).order_by("name"),
            "current": current,
            "counts": services.queue_counts(),
            "videos": services.video_queue(),
            "stories": services.story_queue(),
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
                    game=request.POST.get("game"),
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
                    game=request.POST.get("game"),
                )
                messages.success(request, "Saved.")
        except ValueError as e:
            messages.error(request, str(e))
        return self._back(request)

    def story_act(self, request: HttpRequest, pk: int):
        n = len([k for k in request.POST if k.startswith("block_")])
        blocks = [request.POST.get(f"block_{i}", "") for i in range(n)]
        try:
            services.story_decision(
                pk,
                request.user,
                request.POST.get("action", ""),
                title=request.POST.get("title"),
                dek=request.POST.get("dek"),
                blocks=blocks if n else None,
                reason=request.POST.get("reason", ""),
            )
            messages.success(request, "Story updated.")
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
