import json
from datetime import date

import pytest

from llm.classify import Classification, Fact
from llm.fake import FakeLLMClient
from modules.content import services as content
from modules.content.models import Article, Change, Evidence, Patch, Requirement
from modules.games.models import Release
from modules.ingest import services as ingest
from modules.platform.models import SiteSetting


def art(game, url="https://news.example.com/a", title="t"):
    return Article.objects.create(
        game=game, title=title, source_url=url, canonical_url=url, source_name="X"
    )


def cls(fact=None, confidence=0.95, topic="news", slug="test-game"):
    return Classification(
        game_slug=slug,
        topic=topic,
        confidence=confidence,
        tags=["a"],
        summary="Our own words describing what was announced for players today.",
        fact=fact,
    )


DATE = Fact(kind="release_date", platform="pc", release_date=date(2027, 3, 1))


def test_verification_model():
    assert content.compute_verification(set()) == "rumour"
    assert content.compute_verification({"a.com"}) == "reported"
    assert content.compute_verification({"a.com", "b.com"}) == "confirmed"
    assert content.compute_verification({"a.com"}, has_video=True) == "confirmed"


def test_auto_publish_release_date_above_threshold(game):
    ok, why = content.try_auto_publish_fact(art(game), cls(DATE))
    assert ok, why
    r = Release.objects.get(game=game, is_current=True)
    assert r.date == date(2027, 3, 1) and r.confidence == "reported" and r.source_url
    assert Change.objects.filter(game=game, kind="release").exists()


def test_second_independent_source_upgrades_to_confirmed(game):
    content.try_auto_publish_fact(art(game, "https://one.example.com/a"), cls(DATE))
    content.try_auto_publish_fact(art(game, "https://two.example.org/b"), cls(DATE))
    r = Release.objects.get(game=game, is_current=True)
    assert r.confidence == "confirmed" and r.source_count == 2
    assert Change.objects.filter(game=game, verification="confirmed").exists()


def test_same_domain_twice_is_not_independent(game):
    content.try_auto_publish_fact(art(game, "https://one.example.com/a"), cls(DATE))
    content.try_auto_publish_fact(art(game, "https://www.example.com/b"), cls(DATE))
    assert Release.objects.get(game=game, is_current=True).confidence == "reported"


@pytest.mark.parametrize(
    "c,reason",
    [
        (cls(DATE, confidence=0.5), "below threshold"),
        (cls(DATE, topic="rumour"), "rumour"),
        (cls(None), "no structured fact"),
        (cls(Fact(kind="release_date", platform="ps5", release_date=date(2027, 3, 1))), "not PC"),
    ],
)
def test_not_auto_published(game, c, reason):
    ok, why = content.try_auto_publish_fact(art(game), c)
    assert not ok and reason in why
    assert not Release.objects.filter(game=game).exists()


def test_confirmed_date_not_overridden_by_single_source(game):
    content.try_auto_publish_fact(art(game, "https://one.example.com/a"), cls(DATE))
    content.try_auto_publish_fact(art(game, "https://two.example.org/b"), cls(DATE))
    other = Fact(kind="release_date", platform="pc", release_date=date(2028, 1, 1))
    ok, why = content.try_auto_publish_fact(art(game, "https://three.example.net/c"), cls(other))
    assert not ok and "human review" in why
    assert Release.objects.get(game=game, is_current=True).date == date(2027, 3, 1)


def test_patch_and_requirement_facts(game):
    p = Fact(kind="patch", platform="pc", patch_version="1.02", patch_date=date(2026, 11, 2))
    assert content.try_auto_publish_fact(art(game), cls(p, topic="patch"))[0]
    assert Patch.objects.get(game=game, version="1.02").verification == "reported"
    r = Fact(
        kind="requirement",
        platform="pc",
        req_tier="min",
        cpu="i5-8400",
        gpu="GTX 1060",
        ram_gb=8,
        storage_gb=60,
    )
    assert content.try_auto_publish_fact(
        art(game, "https://n.example.com/r"), cls(r, topic="requirements")
    )[0]
    req = Requirement.objects.get(game=game, tier="min")
    assert req.gpu == "GTX 1060" and not req.is_placeholder


def test_kill_switch_blocks_auto_publish_and_ingest(game, source):
    s = SiteSetting.load()
    s.kill_switch = True
    s.save()
    assert content.try_auto_publish_fact(art(game), cls(DATE))[0] is False
    assert ingest.fetch_and_ingest(source.pk) is None
    a = art(game, "https://news.example.com/n")
    assert ingest.classify_article(a.pk, "lead") == "paused"


def good_json(**kw):
    d = {
        "game_slug": "test-game",
        "topic": "release_date",
        "confidence": 0.95,
        "tags": ["date"],
        "summary": "The studio has named a PC launch day, which moves the tracker from unconfirmed to reported.",
        "fact": {"kind": "release_date", "platform": "pc", "release_date": "2027-03-01"},
    }
    d.update(kw)
    return json.dumps(d)


def test_classify_pipeline_auto_publishes_fact_but_queues_article_for_review(game):
    a = art(game)
    assert (
        ingest.classify_article(a.pk, "lead text", client=FakeLLMClient([good_json()]))
        == "classified"
    )
    a.refresh_from_db()
    assert a.status == "queued" and a.our_summary and "auto-published" in a.review_reason
    assert Release.objects.filter(game=game, date=date(2027, 3, 1)).exists()


def test_classify_invalid_goes_to_review(game):
    a = art(game)
    assert (
        ingest.classify_article(a.pk, "lead", client=FakeLLMClient(["x", "y"])) == "queued-invalid"
    )
    a.refresh_from_db()
    assert a.status == "queued" and "invalid classifier output" in a.review_reason


def test_classify_is_idempotent(game):
    a = art(game)
    fake = FakeLLMClient([good_json()])
    ingest.classify_article(a.pk, "l", client=fake)
    assert ingest.classify_article(a.pk, "l", client=fake) == "skipped"
    assert len(fake.calls) == 1


def test_wrong_game_goes_to_review(game):
    a = art(game)
    ingest.classify_article(a.pk, "l", client=FakeLLMClient([good_json(game_slug=None)]))
    a.refresh_from_db()
    assert a.status == "queued" and not Release.objects.exists()


def test_stuck_articles_are_requeued_not_lost(game):
    from datetime import timedelta

    from django.utils import timezone

    a = art(game)
    Article.objects.filter(pk=a.pk).update(created_at=timezone.now() - timedelta(hours=2))
    assert ingest.requeue_stuck() == 1
    a.refresh_from_db()
    assert a.status == "queued"


def test_approve_requires_our_summary_and_reject_unpublishes(game, user):
    a = art(game)
    with pytest.raises(ValueError):
        content.approve_article(a, user)
    content.approve_article(a, user, summary="Our short summary of the item.", tags=["Dev", "PC"])
    a.refresh_from_db()
    assert a.status == "published" and a.tags == ["dev", "pc"] and a.published_at
    assert Change.objects.filter(subject_kind="article", subject_id=a.pk, is_public=True).exists()
    content.reject_article(a, user, "oops")
    assert not Change.objects.filter(
        subject_kind="article", subject_id=a.pk, is_public=True
    ).exists()


def test_publish_triggers_revalidation_after_commit(
    game, user, django_capture_on_commit_callbacks, monkeypatch
):
    sent = []
    monkeypatch.setattr(
        "modules.platform.services.post_revalidation",
        lambda tags, paths, client=None: sent.append((tags, paths)),
    )
    a = art(game)
    with django_capture_on_commit_callbacks(execute=True):
        content.approve_article(a, user, summary="Our summary of this announcement.")
    assert (
        sent and "news" in sent[0][0] and "game:test-game" in sent[0][0] and "/news" in sent[0][1]
    )


def test_evidence_video_confirms(game):
    r = Release.objects.create(game=game, date=date(2027, 1, 1), confidence="reported")
    content.add_evidence(game, "release", r.pk, "https://one.example.com/x")
    content.add_evidence(
        game, "release", r.pk, "https://www.youtube.com/watch?v=abc", Evidence.Kind.VIDEO
    )
    assert content.recompute_verification("release", r.pk)[1] == "confirmed"
