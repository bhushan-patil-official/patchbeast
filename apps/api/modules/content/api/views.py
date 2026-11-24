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
        "faq": cfg.get("faq", []),
        "checker_enabled": bool(cfg.get("checker", True)),
        "affiliate_categories": cfg.get("affiliate_categories", ["gpu", "ssd", "ram"]),
        "sections": cfg.get("sections", ["release", "requirements", "patches", "videos", "news"]),
        "seo": selectors.seo_for_game(game),
    }  # fmt: skip
    return Response(s.HubSerializer(data).data)


@extend_schema(responses=s.PatchesPageSerializer, tags=["games"])
@api_view(["GET"])
def game_patches(request, slug: str):
    g = _game_or_404(slug)
    return Response(
        s.PatchesPageSerializer(
            {
                "game": g,
                "items": selectors.Patch.objects.filter(game=g),
                "seo": selectors.seo_subpage(g, "patches"),
            }
        ).data
    )


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
        qs = selectors.published_articles().order_by("-published_at")
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
