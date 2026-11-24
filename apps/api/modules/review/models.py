from django.db import models

from modules.common.models import AuditModel
from modules.content.models import Article


class QueuedArticle(Article):
    """Proxy used to mount the review queue in the admin (no table of its own)."""

    class Meta:
        proxy = True
        verbose_name = "review queue"
        verbose_name_plural = "review queue"


class ReviewAction(AuditModel):
    class Action(models.TextChoices):
        APPROVE = "approve"
        REJECT = "reject"
        EDIT = "edit"

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="review_actions")
    action = models.CharField(max_length=10, choices=Action.choices)
    note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-created_at"]
