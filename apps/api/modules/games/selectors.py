from .models import Game, Release


def enabled_games():
    return Game.objects.filter(enabled=True)


def get_game(slug: str) -> Game | None:
    return enabled_games().filter(slug=slug).first()


def current_release(game: Game, platform: str = "pc") -> Release | None:
    return Release.objects.filter(game=game, platform=platform, is_current=True).first()


def release_history(game: Game, platform: str = "pc"):
    return Release.objects.filter(game=game, platform=platform).order_by("-created_at")
