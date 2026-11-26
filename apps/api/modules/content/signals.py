"""Any save/delete of public content refreshes the website, whichever path made the change
(review queue, Django admin form, shell, pipeline). Receivers only SCHEDULE a revalidation after
the surrounding transaction commits; the Next.js side re-renders on the next request."""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from modules.games.models import Game, Release
from modules.platform.services import request_revalidation

from .models import Article, Patch, Requirement, Story, Video
from .services import game_tags, request_indexnow


def _game_paths(game: Game) -> list[str]:
    slug = game.slug
    paths = [
        "/",
        "/news",
        f"/games/{slug}",
        f"/games/{slug}/news",
        f"/games/{slug}/patches",
        f"/games/{slug}/timeline",
    ]
    if game.vanity_path:
        paths.append(f"/{game.vanity_path}")
    return paths


def _refresh(game: Game | None, *extra_tags: str, paths: tuple[str, ...] = ()) -> None:
    if game is None:
        request_revalidation(["news", *extra_tags], ["/news", *paths])
        return
    all_paths = [*_game_paths(game), *paths]
    request_revalidation([*game_tags(game), *extra_tags], all_paths)
    request_indexnow(all_paths)


@receiver(pre_save, sender=Article)
@receiver(pre_save, sender=Story)
@receiver(pre_save, sender=Video)
def _remember_published(sender, instance, raw=False, **kwargs):
    """Was this row public before the save? (so un-publishing also refreshes the site)"""
    instance._was_public = bool(
        instance.pk and sender.objects.filter(pk=instance.pk, status="published").exists()
    )


@receiver(post_save, sender=Article)
@receiver(post_delete, sender=Article)
def _article(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if instance.status == Article.Status.PUBLISHED or getattr(instance, "_was_public", False):
        _refresh(instance.game, "news")


@receiver(post_save, sender=Story)
@receiver(post_delete, sender=Story)
def _story(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if instance.status == Story.Status.PUBLISHED or getattr(instance, "_was_public", False):
        _refresh(
            instance.game,
            "news",
            "stories",
            paths=(f"/games/{instance.game.slug}/news/{instance.slug}",),
        )


@receiver(post_save, sender=Video)
@receiver(post_delete, sender=Video)
def _video(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if instance.status == Video.Status.PUBLISHED or getattr(instance, "_was_public", False):
        _refresh(instance.game, "videos")


@receiver(post_save, sender=Patch)
@receiver(post_delete, sender=Patch)
@receiver(post_save, sender=Requirement)
@receiver(post_delete, sender=Requirement)
@receiver(post_save, sender=Release)
@receiver(post_delete, sender=Release)
def _facts(sender, instance, raw=False, **kwargs):
    if raw:
        return
    extra = ()
    if isinstance(instance, Patch):
        extra = (f"/games/{instance.game.slug}/patches/{instance.platform}/{instance.version}",)
    _refresh(instance.game, paths=extra)


@receiver(post_save, sender=Game)
def _game(sender, instance, raw=False, **kwargs):
    if not raw:
        _refresh(instance, "config")
