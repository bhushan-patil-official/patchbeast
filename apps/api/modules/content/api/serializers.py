from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.common.choices import Verification
from modules.content import selectors
from modules.content.models import Article, Change, Patch, Requirement, Video
from modules.games.models import Game, Release


class SeoSerializer(serializers.Serializer):
    indexable = serializers.BooleanField()
    reason = serializers.CharField(allow_blank=True)


class ReleaseSerializer(serializers.ModelSerializer):
    countdown_mode = serializers.SerializerMethodField()
    confidence = serializers.ChoiceField(choices=Verification.choices)

    class Meta:
        model = Release
        fields = [
            "id",
            "platform",
            "date",
            "confidence",
            "source_url",
            "source_count",
            "note",
            "is_placeholder",
            "created_at",
            "countdown_mode",
        ]

    @extend_schema_field(serializers.ChoiceField(choices=["live", "unconfirmed"]))
    def get_countdown_mode(self, r: Release) -> str:
        """'live' only when a date exists and is Reported/Confirmed and not a placeholder."""
        ok = r.date and r.confidence != Verification.RUMOUR and not r.is_placeholder
        return "live" if ok else "unconfirmed"


class ChangeSerializer(serializers.ModelSerializer):
    game_slug = serializers.CharField(source="game.slug")
    game_name = serializers.CharField(source="game.name")
    verification = serializers.ChoiceField(choices=Verification.choices)

    class Meta:
        model = Change
        fields = [
            "id",
            "game_slug",
            "game_name",
            "kind",
            "title",
            "detail",
            "version_label",
            "source_url",
            "verification",
            "occurred_at",
        ]


class PatchSerializer(serializers.ModelSerializer):
    verification = serializers.ChoiceField(choices=Verification.choices)

    class Meta:
        model = Patch
        fields = [
            "id",
            "version",
            "date",
            "notes_url",
            "our_summary",
            "verification",
            "source_count",
            "is_placeholder",
        ]


class RequirementSerializer(serializers.ModelSerializer):
    verification = serializers.ChoiceField(choices=Verification.choices)

    class Meta:
        model = Requirement
        fields = ["id", "platform", "tier", "os", "cpu", "gpu", "ram_gb", "storage_gb", "cpu_ref", "gpu_ref", "notes", "source_url",
                  "verification", "source_count", "is_placeholder"]  # fmt: skip


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "youtube_id", "title", "channel", "kind", "published_at", "is_placeholder"]


class ArticleSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField())
    game_slug = serializers.CharField(source="game.slug")
    game_name = serializers.CharField(source="game.name")
    verification = serializers.ChoiceField(choices=Verification.choices)

    class Meta:
        model = Article
        fields = ["id", "game_slug", "game_name", "title", "source_url", "source_name", "our_summary", "tags", "topic", "verification",
                  "status", "published_at", "created_at"]  # fmt: skip


class FaqSerializer(serializers.Serializer):
    q = serializers.CharField()
    a = serializers.CharField()


class GameCardSerializer(serializers.ModelSerializer):
    release = serializers.SerializerMethodField()
    latest_changes = serializers.SerializerMethodField()
    seo = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "slug",
            "name",
            "short_name",
            "tagline",
            "platform",
            "is_placeholder",
            "release",
            "latest_changes",
            "seo",
        ]

    @extend_schema_field(ReleaseSerializer(allow_null=True))
    def get_release(self, g: Game):
        from modules.games.selectors import current_release

        r = current_release(g)
        return ReleaseSerializer(r).data if r else None

    @extend_schema_field(ChangeSerializer(many=True))
    def get_latest_changes(self, g: Game):
        return ChangeSerializer(
            selectors.public_changes(g, confirmed_only=True)[:3], many=True
        ).data

    @extend_schema_field(SeoSerializer)
    def get_seo(self, g: Game):
        return selectors.seo_for_game(g)


class HubSerializer(serializers.Serializer):
    game = GameCardSerializer()
    release = ReleaseSerializer(allow_null=True)
    release_history = ReleaseSerializer(many=True)
    requirements = RequirementSerializer(many=True)
    patches = PatchSerializer(many=True)
    videos = VideoSerializer(many=True)
    changes = ChangeSerializer(many=True)
    news = ArticleSerializer(many=True)
    faq = FaqSerializer(many=True)
    checker_enabled = serializers.BooleanField()
    affiliate_categories = serializers.ListField(child=serializers.CharField())
    sections = serializers.ListField(child=serializers.CharField())
    seo = SeoSerializer()


class SubpageSerializer(serializers.Serializer):
    game = GameCardSerializer()
    seo = SeoSerializer()


class PatchesPageSerializer(SubpageSerializer):
    items = PatchSerializer(many=True)


class VideosPageSerializer(SubpageSerializer):
    items = VideoSerializer(many=True)


class RequirementsPageSerializer(SubpageSerializer):
    items = RequirementSerializer(many=True)
    release = ReleaseSerializer(allow_null=True)


class SitemapEntrySerializer(serializers.Serializer):
    path = serializers.CharField()
    lastmod = serializers.DateTimeField(allow_null=True)
