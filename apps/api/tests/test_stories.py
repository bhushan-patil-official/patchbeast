import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from llm.fake import FakeLLMClient
from llm.writer import StoryDraft, StoryFailed, StoryInput, validate_draft, write_story
from modules.content import clustering, stories
from modules.content.models import Article, Change, Story
from modules.platform.models import FeatureFlag, SiteSetting

# ---------- clustering ----------
D = clustering.Doc


def test_similar_items_cluster_and_unrelated_does_not():
    docs = [
        D(1, "Update 01.002.002 fixes crashes autosave PlayStation 5", "forbes.com"),
        D(2, "Patch 01.002.002 released with crash fixes and autosave repair", "opencritic.com"),
        D(3, "Studio reveals soundtrack artists and track list", "ign.com"),
        D(4, "Soundtrack track list revealed with artists named", "gamespot.com"),
    ]
    groups = clustering.cluster(docs)
    assert sorted(map(sorted, groups)) == [[1, 2], [3, 4]]


def test_single_outlet_clusters_are_dropped():
    docs = [
        D(1, "Patch 01.002.002 fixes crashes", "a.com"),
        D(2, "Patch 01.002.002 crash fixes released", "a.com"),
    ]
    assert clustering.cluster(docs) == []  # one outlet is not independent corroboration


def test_cluster_size_is_capped():
    docs = [D(i, "Patch 01.002.002 fixes crashes autosave", f"o{i}.com") for i in range(12)]
    assert all(len(g) <= 8 for g in clustering.cluster(docs, max_size=8))


# ---------- writer validation ----------
ITEMS = [
    StoryInput(
        0,
        "Update 01.002.002 fixes crashes",
        "A patch numbered 01.002.002 fixes several crashes and an autosave problem for players on PS5.",
        "Forbes",
        "2026-11-23",
    ),
    StoryInput(
        1,
        "Patch 01.002.002 is out with bug fixes",
        "The 01.002.002 update is about 604 MB on PS5 and fixes crashes and weather bugs.",
        "OpenCritic",
        "2026-11-23",
    ),
]
P1 = (
    "Reports describe version 01.002.002 as a modest stability release. Coverage points to repairs for several crashes and a fault affecting "
    "autosaving on PS5, while neither outlet quotes the publisher directly, so the exact scope remains unclear for now. Details may change as more coverage appears."
)
P2 = (
    "One outlet puts the download at roughly 604 MB on PS5. A second report adds that a weather-related glitch was addressed. "
    "Readers should check the publisher's own support page for the authoritative list of changes before relying on this summary. We will update the briefing if anything changes."
)


def draft(**over):
    d = {
        "title": "Update 01.002.002 brings crash and autosave fixes",
        "dek": "Two outlets report a small update that tackles crashes, an autosave fault and a weather glitch.",
        "blocks": [{"text": P1, "sources": [0]}, {"text": P2, "sources": [1, 0]}],
        "key_points": ["Version 01.002.002", "About 604 MB on PS5"],
        "tags": ["Patch", "PS5"],
    }
    d.update(over)
    return d


def test_valid_draft_passes():
    c = write_story(FakeLLMClient([json.dumps(draft())]), "G", ITEMS, [])
    assert c.tags == ["patch", "ps5"]


@pytest.mark.parametrize(
    "bad,why",
    [
        (
            draft(blocks=[{"text": P1, "sources": [0]}, {"text": P2, "sources": [0]}]),
            "two different",
        ),
        (
            draft(blocks=[{"text": P1, "sources": [7]}, {"text": P2, "sources": [1]}]),
            "unknown item",
        ),
        (
            draft(
                blocks=[
                    {"text": P1.replace("01.002.002", "01.002.009"), "sources": [0]},
                    {"text": P2, "sources": [1]},
                ]
            ),
            "numbers not present",
        ),
        (
            draft(
                blocks=[
                    {"text": P1 + " This is a shocking development.", "sources": [0]},
                    {"text": P2, "sources": [1]},
                ]
            ),
            "clickbait",
        ),
        (
            draft(
                blocks=[
                    {
                        "text": P1
                        + " A patch numbered 01.002.002 fixes several crashes and an autosave problem for players on PS5.",
                        "sources": [0],
                    },
                    {"text": P2, "sources": [1]},
                ]
            ),
            "copies",
        ),
    ],
)
def test_grounding_rules_reject(bad, why):
    with pytest.raises(StoryFailed) as e:
        write_story(FakeLLMClient([json.dumps(bad), json.dumps(bad)]), "G", ITEMS, [])
    assert why in e.value.reason


def test_too_short_is_rejected():
    short = draft(
        blocks=[
            {
                "text": "Version 01.002.002 fixes crashes on PS5 according to reports from outlets.",
                "sources": [0],
            },
            {
                "text": "About 604 MB on PS5 in total according to one of the reports we saw.",
                "sources": [1],
            },
        ]
    )
    with pytest.raises(StoryFailed, match="length"):
        write_story(FakeLLMClient([json.dumps(short)] * 2), "G", ITEMS, [])


def test_retry_once_with_error_feedback_then_success():
    fake = FakeLLMClient(["not json", json.dumps(draft())])
    write_story(fake, "G", ITEMS, [])
    assert len(fake.calls) == 2 and "rejected" in fake.calls[1][1]


def test_prompt_fences_inputs_as_data():
    fake = FakeLLMClient([json.dumps(draft())])
    write_story(fake, "G", ITEMS, ["Patch 01.002.002 (reported)"])
    system, user = fake.calls[0]
    assert "DATA" in system and "<items>" in user and "<facts>" in user and "[0]" in user


def test_validate_draft_directly():
    validate_draft(StoryDraft.model_validate(draft()), ITEMS, [])


# ---------- pipeline ----------
def mk(game, title, summary, url, status="queued", days=1):
    return Article.objects.create(
        game=game, title=title, our_summary=summary, source_url=url, canonical_url=url, source_name=url.split("/")[2], status=status,
        created_at=timezone.now(), source_published_at=timezone.now() - timedelta(days=days),
    )  # fmt: skip


@pytest.fixture
def cluster_articles(game):
    a = mk(game, ITEMS[0].title, ITEMS[0].summary, "https://forbes.example.com/a")
    b = mk(game, ITEMS[1].title, ITEMS[1].summary, "https://opencritic.example.org/b")
    c = mk(
        game,
        "Studio reveals soundtrack artists",
        "The studio named the artists behind the soundtrack and shared a track list.",
        "https://ign.example.net/c",
    )
    return a, b, c


def fake_ok():
    return FakeLLMClient(lambda s, u: json.dumps(draft()))


def test_builds_one_draft_from_a_cluster_and_is_idempotent(game, cluster_articles):
    made = stories.build_for_game(game, fake_ok())
    assert len(made) == 1
    st = made[0]
    assert st.status == "draft" and st.verification == "confirmed" and len(st.sources) == 2
    assert {s["article_id"] for s in st.sources} == {
        cluster_articles[0].pk,
        cluster_articles[1].pk,
    }  # unrelated article excluded
    assert set(st.articles.values_list("pk", flat=True)) == {
        cluster_articles[0].pk,
        cluster_articles[1].pk,
    }
    assert st.model == "fake-model" and st.published_at is None  # NEVER auto-published
    assert stories.build_for_game(game, fake_ok()) == []  # members are in a live story now


def test_invalid_writer_output_creates_no_draft(game, cluster_articles):
    assert stories.build_for_game(game, FakeLLMClient(["nope", "nope"])) == []
    assert not Story.objects.exists()


def test_kill_switch_flag_and_daily_cap_stop_drafting(game, cluster_articles, settings):
    s = SiteSetting.load()
    s.kill_switch = True
    s.save()
    assert stories.build_for_game(game, fake_ok()) == []
    s.kill_switch = False
    s.save()
    FeatureFlag.objects.create(key="stories", enabled=False)
    assert stories.build_for_game(game, fake_ok()) == []
    FeatureFlag.objects.filter(key="stories").update(enabled=True)
    settings.PB = {**settings.PB, "STORY_MAX_PER_DAY": 0}
    assert stories.build_for_game(game, fake_ok()) == []


def test_rejected_articles_and_single_source_are_not_used(game):
    mk(game, ITEMS[0].title, ITEMS[0].summary, "https://forbes.example.com/a")
    mk(game, ITEMS[1].title, ITEMS[1].summary, "https://forbes.example.com/b")  # same outlet
    assert stories.build_for_game(game, fake_ok()) == []
    mk(game, ITEMS[1].title, ITEMS[1].summary, "https://x.example.org/r", status="rejected")
    assert stories.build_for_game(game, fake_ok()) == []


def test_celery_task_runs_through_guard_without_key(game, cluster_articles):
    from modules.content.tasks import build_stories

    assert (
        build_stories() == 0
    )  # test settings use the keyless fake provider ("{}"): invalid output, so nothing is drafted
    assert not Story.objects.exists()


# ---------- review + publish ----------
@pytest.fixture
def draft_story(game, cluster_articles):
    return stories.build_for_game(game, fake_ok())[0]


def test_review_page_shows_drafts_with_sources(client, user, draft_story):
    client.force_login(user)
    r = client.get(reverse("admin:review_queuedarticle_changelist"))
    assert (
        r.status_code == 200
        and draft_story.title.encode() in r.content
        and b"Story drafts" in r.content
    )
    assert b"forbes.example.com" in r.content


def test_approve_with_edit_publishes_and_records_change(
    client, user, draft_story, django_capture_on_commit_callbacks, monkeypatch
):
    sent = []
    monkeypatch.setattr(
        "modules.platform.services.post_revalidation", lambda t, p, client=None: sent.append((t, p))
    )
    client.force_login(user)
    with django_capture_on_commit_callbacks(execute=True):
        client.post(reverse("admin:review_story_act", args=[draft_story.pk]),
                    {"action": "approve", "title": "Edited briefing title for the update", "dek": draft_story.dek, "block_0": P1, "block_1": P2 + " Edited."})  # fmt: skip
    draft_story.refresh_from_db()
    assert (
        draft_story.status == "published"
        and draft_story.title.startswith("Edited")
        and draft_story.reviewed_by == user
    )
    assert draft_story.blocks[1]["text"].endswith("Edited.") and draft_story.blocks[1][
        "sources"
    ] == [
        1,
        0,
    ]  # citations preserved
    assert Change.objects.filter(
        subject_kind="story", subject_id=draft_story.pk, is_public=True
    ).exists()
    assert any(
        f"/games/{draft_story.game.slug}/news/{draft_story.slug}" in paths for _tags, paths in sent
    )


def test_reject_frees_articles_for_reclustering(client, user, draft_story, game):
    client.force_login(user)
    client.post(
        reverse("admin:review_story_act", args=[draft_story.pk]),
        {"action": "reject", "reason": "inaccurate"},
    )
    draft_story.refresh_from_db()
    assert draft_story.status == "rejected" and draft_story.articles.count() == 0
    assert (
        len(stories.build_for_game(game, fake_ok())) == 0
    )  # same cluster_key already exists: no duplicate draft


def test_anonymous_cannot_act_on_stories(client, draft_story):
    r = client.post(reverse("admin:review_story_act", args=[draft_story.pk]), {"action": "approve"})
    assert r.status_code == 302 and "login" in r["Location"]
    draft_story.refresh_from_db()
    assert draft_story.status == "draft"


# ---------- public API ----------
def publish(story, user):
    stories.approve_story(story, user)
    return story


def test_api_exposes_only_published_stories(client, draft_story, user):
    assert client.get("/api/v1/stories/").json()["results"] == []
    assert (
        client.get(f"/api/v1/games/{draft_story.game.slug}/stories/{draft_story.slug}/").status_code
        == 404
    )  # drafts are private
    publish(draft_story, user)
    lst = client.get("/api/v1/stories/").json()["results"]
    assert (
        [s["slug"] for s in lst] == [draft_story.slug]
        and lst[0]["source_count"] == 2
        and lst[0]["verification"] == "confirmed"
    )
    d = client.get(f"/api/v1/games/{draft_story.game.slug}/stories/{draft_story.slug}/").json()
    assert len(d["blocks"]) == 2 and len(d["sources"]) == 2 and d["blocks"][1]["sources"] == [1, 0]
    assert d["seo"]["indexable"] is True or d["seo"]["indexable"] is False  # present
    assert client.get(f"/api/v1/stories/?game={draft_story.game.slug}").json()["count"] == 1
    assert client.get("/api/v1/stories/?game=nope").json()["count"] == 0


def test_hub_and_sitemap_include_published_story(client, draft_story, user):
    from datetime import date

    from modules.content import services as content
    from modules.games.models import Release

    Release.objects.create(
        game=draft_story.game,
        platform="pc",
        date=date.today() + timedelta(days=9),
        confidence="reported",
        source_url="https://a.example.com",
    )
    publish(draft_story, user)
    hub = client.get(f"/api/v1/games/{draft_story.game.slug}/").json()
    assert [s["slug"] for s in hub["stories"]] == [draft_story.slug]
    paths = {e["path"] for e in client.get("/api/v1/sitemap/").json()}
    assert f"/games/{draft_story.game.slug}/news/{draft_story.slug}" in paths
    assert content  # imported for side-effect-free clarity


def test_unpublished_game_story_not_in_sitemap(client, draft_story):
    paths = {e["path"] for e in client.get("/api/v1/sitemap/").json()}
    assert not any(draft_story.slug in p for p in paths)
