import secrets

from django.db import models

from modules.common.models import AuditModel


def _token() -> str:
    return secrets.token_urlsafe(32)


class Subscriber(AuditModel):
    email = models.EmailField(unique=True)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    confirm_token = models.CharField(max_length=64, unique=True, default=_token)
    unsub_token = models.CharField(max_length=64, unique=True, default=_token)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    signup_source = models.CharField(max_length=60, blank=True)
    last_digest_week = models.CharField(max_length=10, blank=True)
    games = models.JSONField(default=list, blank=True, help_text="game slugs; empty = all games")

    def __str__(self) -> str:
        return self.email

    @property
    def active(self) -> bool:
        return self.confirmed and self.unsubscribed_at is None


class DigestRun(AuditModel):
    iso_week = models.CharField(max_length=10, unique=True)
    recipients = models.PositiveIntegerField(default=0)
    sent = models.PositiveIntegerField(default=0)
    item_count = models.PositiveIntegerField(default=0)
