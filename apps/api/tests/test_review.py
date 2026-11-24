from django.urls import reverse

from modules.content.models import Article, Video
from modules.review.models import ReviewAction


def queued(game, i=1):
    return Article.objects.create(
        game=game,
        title=f"T{i}",
        source_url=f"https://x.example.com/{i}",
        canonical_url=f"https://x.example.com/{i}",
        status="queued",
        our_summary="Our summary.",
        review_reason="needs human review",
    )


def test_queue_page_renders_with_keyboard_help(client, user, game):
    queued(game)
    client.force_login(user)
    r = client.get(reverse("admin:review_queuedarticle_changelist"))
    assert (
        r.status_code == 200 and b"Approve &amp; publish" in r.content and b"keydown" in r.content
    )


def test_one_click_approve_with_edit_and_reject(client, user, game):
    a, b = queued(game, 1), queued(game, 2)
    client.force_login(user)
    url = lambda pk: reverse("admin:review_act", args=[pk])
    client.post(
        url(a.pk),
        {"action": "approve", "title": "Edited", "summary": "Better summary.", "tags": "A, b"},
    )
    client.post(url(b.pk), {"action": "reject", "reason": "dupe"})
    a.refresh_from_db()
    b.refresh_from_db()
    assert (a.status, a.title, a.tags, a.reviewed_by) == ("published", "Edited", ["a", "b"], user)
    assert b.status == "rejected"
    assert set(ReviewAction.objects.values_list("action", flat=True)) == {"approve", "reject"}


def test_anonymous_cannot_use_queue(client, game):
    a = queued(game)
    r = client.post(reverse("admin:review_act", args=[a.pk]), {"action": "approve", "summary": "x"})
    assert r.status_code == 302 and "login" in r["Location"]
    a.refresh_from_db()
    assert a.status == "queued"


def test_video_approval(client, user, game):
    v = Video.objects.create(game=game, youtube_id="v1", title="V", status="queued")
    client.force_login(user)
    client.post(reverse("admin:review_video_act", args=[v.pk]), {"action": "approve"})
    v.refresh_from_db()
    assert v.status == "published"
