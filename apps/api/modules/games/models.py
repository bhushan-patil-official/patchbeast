from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from modules.common.choices import Verification
from modules.common.models import AuditModel
from modules.common.platforms import PLATFORMS, RESERVED_PATHS


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
    allow_index = models.BooleanField(
        default=True, help_text="Master switch: False forces noindex."
    )
    hub_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='e.g. {"faq": [{"q": "...", "a": "..."}], "sections": ["release","requirements","patches","videos","news"], '
        '"checker": true, "affiliate_categories": ["gpu","ssd"]}',
    )
    aliases = models.JSONField(
        default=list, blank=True,
        help_text='Other names used in headlines, e.g. ["GTA 6", "GTA VI", "Grand Theft Auto 6"]. Used to attach articles to this game.',
    )  # fmt: skip
    vanity_path = models.SlugField(
        max_length=60, unique=True, null=True, blank=True,
        help_text="Optional short URL for a flagship page, e.g. 'gta-6-pc' -> /gta-6-pc (the /games/<slug> URL then redirects).",
    )  # fmt: skip
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.vanity_path and self.vanity_path.lower() in RESERVED_PATHS:
            raise ValidationError({"vanity_path": "This path is reserved by the site."})

    def save(self, *args, **kwargs):
        self.vanity_path = (self.vanity_path or "").strip().lower() or None
        super().save(*args, **kwargs)

    @property
    def platforms(self) -> list[str]:
        """Tracked platforms from hub_config (PC first). Defaults to the game's primary platform."""
        raw = (self.hub_config or {}).get("platforms") or [self.platform]
        out = [p for p in raw if p in PLATFORMS]
        if self.platform in PLATFORMS and self.platform not in out:
            out.insert(0, self.platform)
        out.sort(key=lambda p: (p != "pc", list(PLATFORMS).index(p)))
        return out or ["pc"]


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
                fields=["game", "platform"],
                condition=Q(is_current=True),
                name="one_current_release",
            )
        ]

    def __str__(self) -> str:
        return f"{self.game} {self.platform} {self.date or 'TBA'} ({self.confidence})"
