from django.db import models
from django.db.models import Q

from modules.common.choices import Verification
from modules.common.models import AuditModel


class Game(AuditModel):
    """A launch anchor. Pure data: a new game is rows, never code."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=80, blank=True)
    tagline = models.CharField(max_length=240, blank=True)
    platform = models.CharField(max_length=20, default="pc")
    enabled = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(
        default=False, help_text="Seeded placeholder: page stays noindex until real content exists."
    )
    allow_index = models.BooleanField(default=True, help_text="Master switch: False forces noindex.")
    hub_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='e.g. {"faq": [{"q": "...", "a": "..."}], "sections": ["release","requirements","patches","videos","news"], '
        '"checker": true, "affiliate_categories": ["gpu","ssd"]}',
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Release(AuditModel):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="releases")
    platform = models.CharField(max_length=20, default="pc")
    date = models.DateField(null=True, blank=True, help_text="Empty = no date known")
    confidence = models.CharField(
        max_length=10, choices=Verification.choices, default=Verification.RUMOUR
    )
    source_url = models.URLField(max_length=1000, blank=True)
    source_count = models.PositiveSmallIntegerField(default=0)
    is_current = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False)
    note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "platform"], condition=Q(is_current=True), name="one_current_release"
            )
        ]

    def __str__(self) -> str:
        return f"{self.game} {self.platform} {self.date or 'TBA'} ({self.confidence})"
