from .models import Game, Release


def enabled_games():
    return Game.objects.filter(enabled=True)


def get_game(slug: str) -> Game | None:
    return enabled_games().filter(slug=slug).first()


def current_release(game: Game, platform: str = "pc") -> Release | None:
    return Release.objects.filter(game=game, platform=platform, is_current=True).first()


def release_history(game: Game, platform: str | None = None):
    qs = Release.objects.filter(game=game)
    if platform:
        qs = qs.filter(platform=platform)
    return qs.order_by("-created_at")


def current_releases(game: Game) -> list[Release]:
    """Current release row per tracked platform, in display order (PC first)."""
    rows = {r.platform: r for r in Release.objects.filter(game=game, is_current=True)}
    return [rows[p] for p in game.platforms if p in rows]


def hub_path(game: Game) -> str:
    return f"/{game.vanity_path}" if game.vanity_path else f"/games/{game.slug}"
