from django.db import models
from django.utils import timezone

from modules.common.models import AuditModel
from modules.games.models import Game


class Source(AuditModel):
    class Type(models.TextChoices):
        RSS = "rss", "RSS / Atom feed"
        API = "api", "JSON API"
        YOUTUBE = "youtube", "YouTube channel (Data API)"
        WEBSUB = "websub", "WebSub (push)"

    class Health(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        OK = "ok", "OK"
        DEGRADED = "degraded", "Degraded"
        FAILING = "failing", "Failing"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="sources")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.RSS)
    url = models.URLField(max_length=1000, blank=True)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="rss: {} | api: {items_path,title_field,url_field,date_field,lead_field} | "
        "youtube: {channel_id, trusted_channel} | websub: {channel_id, secret}",
    )
    official_feed = models.BooleanField(
        default=False, help_text="Feed intended for machine consumption: skip robots.txt check."
    )
    enabled = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False)
    interval_minutes = models.PositiveSmallIntegerField(default=10)
    next_fetch_at = models.DateTimeField(default=timezone.now, db_index=True)
    # conditional GET state
    etag = models.CharField(max_length=300, blank=True)
    last_modified = models.CharField(max_length=100, blank=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    health = models.CharField(max_length=10, choices=Health.choices, default=Health.UNKNOWN)
    consecutive_failures = models.PositiveIntegerField(default=0)
    failing_since = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["game", "name"]

    def __str__(self) -> str:
        return f"{self.name} [{self.type}]"
