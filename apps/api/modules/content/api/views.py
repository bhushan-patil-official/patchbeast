from django.db.models import F
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from modules.content import selectors
from modules.games import selectors as games_selectors

from . import serializers as s


def _game_or_404(slug: str):
    game = games_selectors.get_game(slug)
    if not game:
        raise NotFound("game not found")
    return game


@extend_schema(responses=s.GameCardSerializer(many=True), tags=["games"])
@api_view(["GET"])
def games_list(request):
    return Response(s.GameCardSerializer(games_selectors.enabled_games(), many=True).data)


@extend_schema(responses=s.HubSerializer, tags=["games"])
@api_view(["GET"])
def game_hub(request, slug: str):
    game = _game_or_404(slug)
    h = selectors.hub_for_game(game)
    cfg = game.hub_config or {}
    data = {
        "game": game, **h,
        "platforms": selectors.platform_options(game),
        "seo_title": cfg.get("seo_title", ""),
        "seo_description": cfg.get("seo_description", ""),
        "faq": cfg.get("faq", []),
        "checker_enabled": bool(cfg.get("checker", True)),
        "affiliate_categories": cfg.get("affiliate_categories", ["gpu", "ssd", "ram"]),
        "sections": cfg.get("sections", ["release", "requirements", "patches", "videos", "news"]),
        "seo": selectors.seo_for_game(game),
    }  # fmt: skip
    return Response(s.HubSerializer(data).data)


@extend_schema(
    parameters=[OpenApiParameter("platform", str, required=False)],
    responses=s.PatchesPageSerializer,
    tags=["games"],
)
@api_view(["GET"])
def game_patches(request, slug: str):
    g = _game_or_404(slug)
    platform = request.query_params.get("platform", "")
    items = selectors.Patch.objects.filter(game=g)
    if platform in g.platforms:
        items = items.filter(platform=platform)
    else:
        platform = ""
    data = {
        "game": g,
        "items": items,
        "platforms": selectors.platform_options(g),
        "selected_platform": platform,
        "seo": selectors.seo_subpage(g, "patches"),
    }
    return Response(s.PatchesPageSerializer(data).data)


@extend_schema(responses=s.VideosPageSerializer, tags=["games"])
@api_view(["GET"])
def game_videos(request, slug: str):
    g = _game_or_404(slug)
    return Response(
        s.VideosPageSerializer(
            {
                "game": g,
                "items": selectors.published_videos(g),
                "seo": selectors.seo_subpage(g, "videos"),
            }
        ).data
    )


@extend_schema(responses=s.RequirementsPageSerializer, tags=["games"])
@api_view(["GET"])
def game_requirements(request, slug: str):
    g = _game_or_404(slug)
    from modules.content.models import Requirement
    from modules.games.selectors import current_release

    data = {
        "game": g,
        "items": Requirement.objects.filter(game=g),
        "release": current_release(g),
        "seo": selectors.seo_subpage(g, "requirements"),
    }
    return Response(s.RequirementsPageSerializer(data).data)


@extend_schema(responses=s.ChangeSerializer(many=True), tags=["games"])
@api_view(["GET"])
def ticker(request):
    return Response(s.ChangeSerializer(selectors.ticker_changes(10), many=True).data)


@extend_schema(parameters=[OpenApiParameter("game", str, required=False)], tags=["news"])
class NewsList(generics.ListAPIView):
    """Curated (human-approved) items only. Our summary + source link."""

    serializer_class = s.ArticleSerializer

    def get_queryset(self):
        qs = selectors.published_articles().order_by(
            F("published_at").desc(nulls_last=True), "-created_at"
        )
        game = self.request.query_params.get("game")
        return qs.filter(game__slug=game) if game else qs


@extend_schema(tags=["news"])
class FeedList(generics.ListAPIView):
    """Raw aggregate (unreviewed items included). The web page is noindex,nofollow."""

    serializer_class = s.ArticleSerializer

    def get_queryset(self):
        return selectors.feed_articles()


@extend_schema(responses=s.SitemapEntrySerializer(many=True), tags=["seo"])
@api_view(["GET"])
def sitemap(request):
    return Response(s.SitemapEntrySerializer(selectors.sitemap_entries(), many=True).data)


@extend_schema(operation_id="game_patch_detail", responses=s.PatchDetailSerializer, tags=["games"])
@api_view(["GET"])
def patch_detail(request, slug: str, platform: str, version: str):
    g = _game_or_404(slug)
    patch = selectors.Patch.objects.filter(game=g, platform=platform, version=version).first()
    if patch is None:
        raise NotFound("patch not found")
    sources = selectors.patch_sources(patch)
    siblings = selectors.Patch.objects.filter(game=g, version=version).exclude(pk=patch.pk)
    changes = selectors.public_changes(g).filter(subject_kind="patch", subject_id=patch.pk)
    data = {
        "game": g, "patch": patch, "siblings": siblings, "changes": changes[:5],
        "sources": [{"url": e.url, "domain": e.domain, "kind": e.kind} for e in sources],
        "seo": selectors.seo_for_patch(g, patch, len(sources)),
    }  # fmt: skip
    return Response(s.PatchDetailSerializer(data).data)


@extend_schema(tags=["games"])
class GameChangesList(generics.ListAPIView):
    """Full change log (timeline) for one game, newest first, paginated."""

    serializer_class = s.ChangeSerializer

    def get_queryset(self):
        return selectors.public_changes(_game_or_404(self.kwargs["slug"]))


@extend_schema(parameters=[OpenApiParameter("game", str, required=False)], tags=["news"])
class StoriesList(generics.ListAPIView):
    """Our written briefings (human-approved), newest first."""

    serializer_class = s.StoryCardSerializer

    def get_queryset(self):
        qs = selectors.published_stories()
        game = self.request.query_params.get("game")
        return qs.filter(game__slug=game) if game else qs


@extend_schema(responses=s.StoryDetailSerializer, tags=["news"])
@api_view(["GET"])
def story_detail(request, slug: str, story: str):
    g = _game_or_404(slug)
    st = selectors.published_stories(g).filter(slug=story).first()
    if st is None:
        raise NotFound("story not found")
    data = {
        "game": g, "story": st, "blocks": st.blocks, "key_points": st.key_points,
        "sources": st.sources, "seo": selectors.seo_for_story(g, st),
    }  # fmt: skip
    return Response(s.StoryDetailSerializer(data).data)
