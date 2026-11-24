from django.db import models

from modules.common.models import AuditModel
from modules.sources.models import Source


class FetchLog(AuditModel):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="fetch_logs")
    ok = models.BooleanField(default=True)
    not_modified = models.BooleanField(default=False)
    items_seen = models.PositiveIntegerField(default=0)
    items_new = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]
