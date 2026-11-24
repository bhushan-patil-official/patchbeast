"""Regression: approving/publishing content must make it appear on the site, whichever path is used."""

from datetime import date

import pytest
from django.core.management import call_command
from django.urls import reverse

from modules.content.models import Article, Change, Evidence, Patch, Requirement, Video
from modules.games.models import Game, Release


@pytest.fixture
def sent(monkeypatch):
    calls: list[tuple[list[str], list[str]]] = []
    monkeypatch.setattr(
        "modules.platform.services.post_revalidation",
        lambda t, p, client=None: calls.append((t, p)),
    )
    return calls


@pytest.fixture
def art(game):
    return Article.objects.create(game=game, title="Headline", source_url="https://s.example.com/a", canonical_url="https://s.example.com/a",
                                  source_name="s", our_summary="Our own summary of the item.", status="queued")  # fmt: skip


def form(a: Article, **over):
    d = {"game": a.game_id or "", "source": "", "title": a.title, "source_url": a.source_url, "source_name": a.source_name,
         "our_summary": a.our_summary, "tags": "[]", "topic": "", "status": a.status, "confidence": "0.5", "verification": "reported",
         "review_reason": "", "reviewed_by": ""}  # fmt: skip
    for f in ("source_published_at", "published_at", "reviewed_at"):
        d[f"{f}_0"] = d[f"{f}_1"] = ""
    d.update(over)
    return d


def post(client, a, **over):
    return client.post(
        reverse("admin:content_article_change", args=[a.pk]), form(a, **over), follow=True
    )


def paths(sent):
    return {p for _t, ps in sent for p in ps}


def tags(sent):
    return {t for ts, _p in sent for t in ts}


def test_publishing_from_the_admin_form_runs_the_real_publish_logic(
    client, user, art, django_capture_on_commit_callbacks, sent
):
    client.force_login(user)
    with django_capture_on_commit_callbacks(execute=True):
        r = post(client, art, status="published")
    assert "Published" in r.content.decode()
    art.refresh_from_db()
    assert art.status == "published" and art.published_at and art.reviewed_by == user
    assert Evidence.objects.filter(subject_kind="article", subject_id=art.pk).exists()
    assert Change.objects.filter(subject_kind="article", subject_id=art.pk, is_public=True).exists()
    assert (
        "/news" in paths(sent)
        and f"/games/{art.game.slug}/news" in paths(sent)
        and "news" in tags(sent)
    )
    assert [a["title"] for a in client.get("/api/v1/news/").json()["results"]] == ["Headline"]


def test_admin_publish_without_a_summary_is_refused_and_stays_queued(client, user, art):
    Article.objects.filter(pk=art.pk).update(our_summary="")
    art.refresh_from_db()
    client.force_login(user)
    r = post(client, art, status="published", our_summary="")
    art.refresh_from_db()
    assert art.status == "queued" and "Not published" in r.content.decode()
    assert client.get("/api/v1/news/").json()["count"] == 0


def test_unpublishing_and_rejecting_in_admin_removes_the_post(
    client, user, art, django_capture_on_commit_callbacks, sent
):
    client.force_login(user)
    post(client, art, status="published")
    art.refresh_from_db()
    sent.clear()
    with django_capture_on_commit_callbacks(execute=True):
        post(client, art, status="rejected")
    art.refresh_from_db()
    assert art.status == "rejected" and client.get("/api/v1/news/").json()["count"] == 0
    assert not Change.objects.filter(
        subject_kind="article", subject_id=art.pk, is_public=True
    ).exists()
    assert "/news" in paths(sent)


def test_back_to_queued_from_published_hides_it_and_refreshes(
    client, user, art, django_capture_on_commit_callbacks, sent
):
    client.force_login(user)
    post(client, art, status="published")
    art.refresh_from_db()
    sent.clear()
    with django_capture_on_commit_callbacks(execute=True):
        post(client, art, status="queued")
    assert client.get("/api/v1/news/").json()["count"] == 0 and "/news" in paths(sent)
    assert not Change.objects.filter(
        subject_kind="article", subject_id=art.pk, is_public=True
    ).exists()


def test_bulk_publish_action(client, user, game):
    ok = Article.objects.create(
        game=game,
        title="ok",
        source_url="https://a.example.com/1",
        canonical_url="https://a.example.com/1",
        our_summary="s",
        status="queued",
    )
    bad = Article.objects.create(
        game=game,
        title="no summary",
        source_url="https://b.example.org/2",
        canonical_url="https://b.example.org/2",
        status="queued",
    )
    client.force_login(user)
    client.post(
        reverse("admin:content_article_changelist"),
        {"action": "publish_selected", "_selected_action": [ok.pk, bad.pk]},
        follow=True,
    )
    ok.refresh_from_db()
    bad.refresh_from_db()
    assert ok.status == "published" and bad.status == "queued"


def test_a_plain_save_as_published_still_gets_a_date_and_refreshes_the_site(
    art, django_capture_on_commit_callbacks, sent
):
    with django_capture_on_commit_callbacks(execute=True):
        art.status = "published"
        art.save()  # e.g. from a shell, a script or another admin path
    art.refresh_from_db()
    assert art.published_at is not None
    assert "/news" in paths(sent) and "news" in tags(sent)


def test_queued_articles_do_not_trigger_refreshes(art, django_capture_on_commit_callbacks, sent):
    with django_capture_on_commit_callbacks(execute=True):
        art.title = "edited"
        art.save()
    assert sent == []


@pytest.mark.parametrize("make", ["patch", "requirement", "release", "video", "game"])
def test_other_public_content_refreshes_the_site_on_save(
    game, make, django_capture_on_commit_callbacks, sent
):
    with django_capture_on_commit_callbacks(execute=True):
        if make == "patch":
            Patch.objects.create(game=game, version="1.0", date=date.today())
        elif make == "requirement":
            Requirement.objects.create(game=game, tier="min", cpu="x", gpu="y")
        elif make == "release":
            Release.objects.create(
                game=game, platform="pc", date=date.today(), confidence="reported"
            )
        elif make == "video":
            Video.objects.create(game=game, youtube_id="v1", title="t", status="published")
        else:
            game.tagline = "changed"
            game.save()
    assert f"game:{game.slug}" in tags(sent) and f"/games/{game.slug}" in paths(sent)


def test_unpublished_video_does_not_refresh(game, django_capture_on_commit_callbacks, sent):
    with django_capture_on_commit_callbacks(execute=True):
        Video.objects.create(game=game, youtube_id="v2", title="t", status="queued")
    assert sent == []


def test_published_items_without_a_date_still_list_last_not_missing(client, game):
    from django.utils import timezone

    dated = Article.objects.create(
        game=game,
        title="dated",
        source_url="https://a.example.com/d",
        canonical_url="https://a.example.com/d",
        our_summary="s",
        status="published",
    )
    undated = Article.objects.create(
        game=game,
        title="undated",
        source_url="https://a.example.com/u",
        canonical_url="https://a.example.com/u",
        our_summary="s",
        status="published",
    )
    Article.objects.filter(pk=undated.pk).update(published_at=None)  # legacy row
    Article.objects.filter(pk=dated.pk).update(published_at=timezone.now())
    assert [a["title"] for a in client.get("/api/v1/news/").json()["results"]] == [
        "dated",
        "undated",
    ]


def test_revalidate_all_command_covers_news_and_every_game(
    game, django_capture_on_commit_callbacks, sent
):
    Game.objects.create(slug="other", name="Other", vanity_path="other-tracker")
    with django_capture_on_commit_callbacks(execute=True):
        call_command("revalidate_all")
    assert {"news", "ticker", f"game:{game.slug}", "game:other"} <= tags(sent)
    assert {
        "/",
        "/news",
        f"/games/{game.slug}/news",
        "/other-tracker",
        "/games/other/timeline",
    } <= paths(sent)
