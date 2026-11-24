from django.conf import settings
from django.db import models
from django.db.models import Q

from modules.common.choices import Verification
from modules.common.models import AuditModel
from modules.games.models import Game
from modules.sources.models import Source


class SubjectKind(models.TextChoices):
    RELEASE = "release"
    PATCH = "patch"
    REQUIREMENT = "requirement"
    ARTICLE = "article"
    VIDEO = "video"


class Article(AuditModel):
    """A *reference* to somebody else's article. We never store source text:
    title + link + OUR summary + tags."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        QUEUED = "queued", "Queued for review"
        PUBLISHED = "published", "Published"
        REJECTED = "rejected", "Rejected"

    game = models.ForeignKey(
        Game, null=True, blank=True, on_delete=models.CASCADE, related_name="articles",
        help_text="Empty = not matched to a game yet (assign one in the review queue).",
    )  # fmt: skip
    source = models.ForeignKey(
        Source, null=True, blank=True, on_delete=models.SET_NULL, related_name="articles"
    )
    title = models.CharField(max_length=300)
    source_url = models.URLField(max_length=1000)
    canonical_url = models.URLField(max_length=1000)
    source_name = models.CharField(
        max_length=120, blank=True, help_text="Attribution shown to readers"
    )
    our_summary = models.TextField(blank=True, help_text="OUR 2-3 line summary (original wording)")
    tags = models.JSONField(default=list, blank=True)
    topic = models.CharField(max_length=30, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.NEW, db_index=True
    )
    confidence = models.FloatField(default=0.0)
    verification = models.CharField(
        max_length=10, choices=Verification.choices, default=Verification.REPORTED
    )
    simhash = models.BigIntegerField(null=True, blank=True)
    review_reason = models.CharField(max_length=300, blank=True)
    source_published_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["game", "canonical_url"], name="uniq_article_game_url"),
            models.UniqueConstraint(
                fields=["canonical_url"],
                condition=Q(game__isnull=True),
                name="uniq_article_url_unassigned",
            ),
        ]
        indexes = [models.Index(fields=["status", "-published_at"])]

    def __str__(self) -> str:
        return self.title[:80]


class Patch(AuditModel):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="patches")
    platform = models.CharField(max_length=20, default="pc")
    version = models.CharField(max_length=60)
    date = models.DateField(null=True, blank=True)
    notes_url = models.URLField(max_length=1000, blank=True)
    our_summary = models.TextField(blank=True)
    highlights = models.JSONField(
        default=list, blank=True, help_text="Our own short bullets (original wording, max 8)"
    )
    size_note = models.CharField(max_length=120, blank=True, help_text="e.g. '603.7 MB'")
    verification = models.CharField(
        max_length=10, choices=Verification.choices, default=Verification.REPORTED
    )
    source_count = models.PositiveSmallIntegerField(default=1)
    is_placeholder = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "platform", "version"], name="uniq_patch_version"
            )
        ]

    def __str__(self) -> str:
        return f"{self.game} {self.version}"


class Requirement(AuditModel):
    class Tier(models.TextChoices):
        MIN = "min", "Minimum"
        REC = "rec", "Recommended"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="requirements")
    platform = models.CharField(max_length=20, default="pc")
    tier = models.CharField(max_length=3, choices=Tier.choices)
    os = models.CharField(max_length=120, blank=True)
    cpu = models.CharField(max_length=160, blank=True)
    gpu = models.CharField(max_length=160, blank=True)
    ram_gb = models.PositiveSmallIntegerField(null=True, blank=True)
    storage_gb = models.PositiveIntegerField(null=True, blank=True)
    cpu_ref = models.CharField(
        max_length=60, blank=True, help_text="id in the web hardware catalogue"
    )
    gpu_ref = models.CharField(
        max_length=60, blank=True, help_text="id in the web hardware catalogue"
    )
    notes = models.CharField(max_length=300, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    verification = models.CharField(
        max_length=10, choices=Verification.choices, default=Verification.RUMOUR
    )
    source_count = models.PositiveSmallIntegerField(default=0)
    is_placeholder = models.BooleanField(default=False)

    class Meta:
        ordering = ["game", "platform", "tier"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "platform", "tier"], name="uniq_requirement_tier"
            )
        ]


class Video(AuditModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued for review"
        PUBLISHED = "published", "Published"
        REJECTED = "rejected", "Rejected"

    class Kind(models.TextChoices):
        TRAILER = "trailer", "Trailer"
        GAMEPLAY = "gameplay", "Gameplay"
        OTHER = "other", "Other"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="videos")
    source = models.ForeignKey(
        Source, null=True, blank=True, on_delete=models.SET_NULL, related_name="videos"
    )
    youtube_id = models.CharField(max_length=20)
    title = models.CharField(max_length=300)
    channel = models.CharField(max_length=160, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.OTHER)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.QUEUED, db_index=True
    )
    published_at = models.DateTimeField(null=True, blank=True)
    is_placeholder = models.BooleanField(default=False)

    class Meta:
        ordering = ["-published_at"]
        constraints = [models.UniqueConstraint(fields=["game", "youtube_id"], name="uniq_video")]


class Evidence(AuditModel):
    """Independent source supporting a subject. Subject is referenced generically
    (kind + id) so later tiers can attach evidence without touching Phase 1 tables."""

    class Kind(models.TextChoices):
        ARTICLE = "article"
        VIDEO = "video"
        OFFICIAL = "official"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="evidence")
    subject_kind = models.CharField(max_length=12, choices=SubjectKind.choices)
    subject_id = models.PositiveBigIntegerField()
    url = models.URLField(max_length=1000)
    domain = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.ARTICLE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subject_kind", "subject_id", "domain"], name="uniq_evidence_domain"
            )
        ]
        indexes = [models.Index(fields=["subject_kind", "subject_id"])]


class Change(AuditModel):
    """Public change log entry ("patch log"): feeds the timeline, ticker and weekly digest."""

    class Kind(models.TextChoices):
        RELEASE = "release"
        PATCH = "patch"
        REQUIREMENT = "requirement"
        NEWS = "news"
        VIDEO = "video"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="changes")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    title = models.CharField(max_length=240)
    detail = models.CharField(
        max_length=500, blank=True, help_text="what changed, e.g. 'Date: unknown -> 2027-03-01'"
    )
    version_label = models.CharField(max_length=60, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    verification = models.CharField(
        max_length=10, choices=Verification.choices, default=Verification.REPORTED
    )
    occurred_at = models.DateTimeField(db_index=True)
    subject_kind = models.CharField(max_length=12, blank=True)
    subject_id = models.PositiveBigIntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["-occurred_at"]


class Story(AuditModel):
    """OUR written briefing synthesised from 2+ independent linked sources.

    Drafted automatically from our own summaries and verified facts (never from source page text),
    reviewed by a person before publishing. Every paragraph cites its sources."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft (awaiting review)"
        PUBLISHED = "published", "Published"
        REJECTED = "rejected", "Rejected"

    class Kind(models.TextChoices):
        BRIEFING = "briefing", "Briefing (one development)"
        ROUNDUP = "roundup", "Roundup (several developments)"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="stories")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.BRIEFING)
    slug = models.SlugField(max_length=120)
    title = models.CharField(max_length=200)
    dek = models.CharField(max_length=300, blank=True)
    blocks = models.JSONField(default=list, help_text='[{"text": "...", "sources": [0, 1]}]')
    key_points = models.JSONField(default=list, blank=True)
    sources = models.JSONField(
        default=list, help_text='[{"article_id": 1, "url": "...", "name": "...", "title": "..."}]'
    )
    tags = models.JSONField(default=list, blank=True)
    articles = models.ManyToManyField(Article, related_name="stories", blank=True)
    cluster_key = models.CharField(max_length=40, db_index=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    verification = models.CharField(
        max_length=10, choices=Verification.choices, default=Verification.REPORTED
    )
    model = models.CharField(max_length=80, blank=True)
    review_reason = models.CharField(max_length=300, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name_plural = "stories"
        constraints = [
            models.UniqueConstraint(fields=["game", "slug"], name="uniq_story_slug"),
            models.UniqueConstraint(fields=["game", "cluster_key"], name="uniq_story_cluster"),
        ]

    def __str__(self) -> str:
        return self.title[:80]
