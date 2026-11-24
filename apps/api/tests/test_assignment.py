import json
from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from llm.fake import FakeLLMClient
from llm.ports import LLMUnavailable
from modules.content import services as content
from modules.content import stories
from modules.content.models import Article, Story
from modules.games.models import Game
from modules.games.services import match_games
from modules.ingest import services as ingest
from modules.sources.models import Source
from modules.sources.ports import RawItem
from modules.sources.services import due_sources

SUMMARY = "Our own short description of what this item reports for players today."


def cj(**kw):
    d = {
        "game_slug": None,
        "relevant": True,
        "topic": "news",
        "confidence": 0.9,
        "tags": ["x"],
        "summary": SUMMARY,
        "fact": None,
    }
    d.update(kw)
    return json.dumps(d)


@pytest.fixture
def two(db):
    a = Game.objects.create(slug="alpha", name="Alpha Quest", aliases=["AQ2", "Alpha Quest 2"])
    b = Game.objects.create(
        slug="beta", name="Beta Racer (PC)", short_name="Beta", aliases=["Beta Racer 3"]
    )
    return a, b


def art(game, source=None, title="Some headline", url="https://x.example.com/1"):
    return Article.objects.create(
        game=game, source=source, title=title, source_url=url, canonical_url=url, source_name="X"
    )


def src(game=None):
    return Source.objects.create(
        game=game, name="Feed", type="rss", url="https://x.example.com/feed.xml", official_feed=True
    )


def run(article, resp, lead="lead text"):
    return ingest.classify_article(article.pk, lead, client=FakeLLMClient([resp]))


# ---------- name matching ----------
def test_match_games_word_boundaries_and_aliases(two):
    a, b = two
    hits = match_games(
        "Alpha Quest 2 patch lands; AQ2 players rejoice. Beta Racer 3 is unrelated.", [a, b]
    )
    assert hits == {
        "alpha": 2,
        "beta": 1,
    }  # "Alpha Quest" (+ "Alpha Quest 2") and "AQ2"; "Beta Racer 3"
    assert match_games("AQ20 is something else", [a]) == {}  # whole words only
    assert match_games("the beta test begins", [b]) == {}  # short_name < 5 chars is not used
    assert match_games("Beta Racer news", [b]) == {"beta": 1}  # "(PC)" suffix is ignored


# ---------- assignment rules ----------
def test_unsure_model_does_not_override_the_sources_game(two):
    a, _ = two
    x = art(a, src(a))
    assert run(x, cj(game_slug=None)) == "classified"
    x.refresh_from_db()
    assert x.game == a and x.status == "queued" and "could not assign" not in x.review_reason


def test_model_disagreeing_without_name_evidence_keeps_source_game_and_flags_it(two):
    a, b = two
    x = art(a, src(a))
    run(x, cj(game_slug="beta"))
    x.refresh_from_db()
    assert x.game == a and "model suggested Beta Racer" in x.review_reason


def test_model_plus_name_match_reassigns_a_misfiled_article(two):
    a, b = two
    x = art(a, src(a), title="Beta Racer 3 gets a big patch")
    run(x, cj(game_slug="beta"), lead="")
    x.refresh_from_db()
    assert x.game == b


def test_general_feed_uses_the_model_or_a_single_name_match(two):
    a, b = two
    x = art(None, src(None), url="https://x.example.com/2")
    run(x, cj(game_slug="alpha"))
    x.refresh_from_db()
    assert x.game == a
    y = art(None, src(None), title="AQ2 gets a new trailer", url="https://x.example.com/3")
    run(y, cj(game_slug=None), lead="")
    y.refresh_from_db()
    assert y.game == a  # attached by its name alone


def test_nothing_matches_stays_unassigned_with_an_actionable_reason(two):
    x = art(None, src(None), title="Hardware sale this weekend", url="https://x.example.com/4")
    run(x, cj(game_slug=None))
    x.refresh_from_db()
    assert x.game is None and x.status == "queued" and "assign one" in x.review_reason


def test_ambiguous_name_matches_stay_unassigned(two):
    x = art(
        None, src(None), title="AQ2 and Beta Racer 3 both patched", url="https://x.example.com/5"
    )
    run(x, cj(game_slug=None), lead="")
    x.refresh_from_db()
    assert x.game is None


def test_clearly_irrelevant_items_are_rejected_not_queued(two):
    a, _ = two
    x = art(a, src(a), title="Best coffee machines of the year", url="https://x.example.com/6")
    run(x, cj(relevant=False, confidence=0.95))
    x.refresh_from_db()
    assert x.status == "rejected" and "not about a tracked game" in x.review_reason


def test_irrelevant_verdict_is_ignored_when_the_name_appears_or_confidence_is_low(two):
    a, _ = two
    x = art(a, src(a), title="AQ2 discussed in a roundup", url="https://x.example.com/7")
    run(x, cj(relevant=False, confidence=0.95), lead="")
    x.refresh_from_db()
    assert x.status == "queued"
    y = art(a, src(a), title="Something vague", url="https://x.example.com/8")
    run(y, cj(relevant=False, confidence=0.4))
    y.refresh_from_db()
    assert y.status == "queued"


def test_without_the_llm_a_name_match_still_attaches_the_article(two, monkeypatch):
    a, _ = two

    def boom(*args, **kw):
        raise LLMUnavailable("no key")

    monkeypatch.setattr(ingest, "classify", boom)
    x = art(None, src(None), title="Alpha Quest 2 launch window", url="https://x.example.com/9")
    assert ingest.classify_article(x.pk, "", client=FakeLLMClient()) == "queued-unavailable"
    x.refresh_from_db()
    assert x.game == a and "LLM unavailable" in x.review_reason


def test_reassign_conflict_keeps_original_game(two):
    a, b = two
    art(b, None, url="https://x.example.com/dup")  # already filed under beta
    x = art(a, src(a), title="Beta Racer 3 news", url="https://x.example.com/dup")
    run(x, cj(game_slug="beta"), lead="")
    x.refresh_from_db()
    assert x.game == a and "already filed" in x.review_reason


# ---------- general feeds at ingest ----------
def test_general_feed_attaches_by_name_at_ingest_and_dedupes_globally(two):
    a, b = two
    s = src(None)
    items = [
        RawItem(
            title="Alpha Quest 2 patch notes are out", url="https://x.example.com/p1", lead="fixes"
        ),
        RawItem(title="Weekend deals on headsets", url="https://x.example.com/p2", lead="cheap"),
        RawItem(title="Beta Racer 3 trailer", url="https://x.example.com/p3", lead="new"),
    ]
    st = ingest.ingest_items(s, items, dispatch=False)
    assert st.new == 3
    by_url = {x.source_url: x.game for x in Article.objects.all()}
    assert by_url["https://x.example.com/p1"] == a and by_url["https://x.example.com/p3"] == b
    assert by_url["https://x.example.com/p2"] is None
    st2 = ingest.ingest_items(
        src(a),
        [
            RawItem(
                title="Alpha Quest 2 patch notes are out",
                url="https://www.x.example.com/p1/",
                lead="fixes",
            )
        ],
        dispatch=False,
    )
    assert st2.exact_dup == 1 and Article.objects.count() == 3  # same URL is never filed twice


def test_general_sources_are_scheduled(two):
    s = src(None)
    assert s in list(due_sources())


def test_approving_an_unassigned_article_is_refused(db, user):
    x = art(None, None)
    x.our_summary = SUMMARY
    with pytest.raises(ValueError, match="assign a game"):
        content.approve_article(x, user)


# ---------- review UI ----------
def queued(game, i, summary=SUMMARY, url=None):
    u = url or f"https://outlet{i}.com/{i}"
    return Article.objects.create(
        game=game,
        title=f"T{i}",
        source_url=u,
        canonical_url=u,
        source_name=f"o{i}",
        our_summary=summary,
        status="queued",
    )


def test_review_page_filters_by_game_and_unassigned(client, user, two):
    a, b = two
    queued(a, 1), queued(b, 2), queued(None, 3)
    client.force_login(user)
    url = reverse("admin:review_queuedarticle_changelist")
    allp = client.get(url).content
    assert b"T1" in allp and b"T2" in allp and b"T3" in allp and b"choose one" in allp
    only_a = client.get(url + "?game=alpha").content
    assert b"T1" in only_a and b"T2" not in only_a
    un = client.get(url + "?game=unassigned").content
    assert b"T3" in un and b"T1" not in un


def test_assign_a_game_and_approve_in_one_click(client, user, two):
    a, _ = two
    x = queued(None, 1)
    client.force_login(user)
    r = client.post(
        reverse("admin:review_act", args=[x.pk]),
        {"action": "approve", "game": "alpha", "title": x.title, "summary": SUMMARY, "tags": "a"},
    )
    assert r.status_code == 302
    x.refresh_from_db()
    assert x.game == a and x.status == "published"


def test_unassigned_approve_without_a_game_shows_an_error_and_stays_queued(client, user, two):
    x = queued(None, 1)
    client.force_login(user)
    client.post(
        reverse("admin:review_act", args=[x.pk]),
        {"action": "approve", "game": "", "title": x.title, "summary": SUMMARY},
    )
    x.refresh_from_db()
    assert x.status == "queued"


def test_bulk_reject_and_approve_linked(client, user, two):
    a, _ = two
    r1, r2, ok, no_game = queued(a, 1), queued(a, 2), queued(a, 3), queued(None, 4)
    client.force_login(user)
    url = reverse("admin:review_bulk")
    client.post(url, {"action": "reject", "ids": [r1.pk, r2.pk]})
    assert Article.objects.filter(status="rejected").count() == 2
    client.post(url, {"action": "approve_linked", "ids": [ok.pk, no_game.pk]})
    ok.refresh_from_db()
    no_game.refresh_from_db()
    assert (
        ok.status == "published" and no_game.status == "queued"
    )  # the unassigned one is skipped, not lost


def fake_story_writer():
    from .test_stories import P1, P2, draft

    return FakeLLMClient(lambda s, u: json.dumps(draft()))


def test_bulk_merge_writes_one_briefing_draft(client, user, two, monkeypatch):
    a, _ = two
    from .test_stories import ITEMS

    x = queued(a, 1, summary=ITEMS[0].summary)
    y = queued(a, 2, summary=ITEMS[1].summary)
    x.title, y.title = ITEMS[0].title, ITEMS[1].title
    x.save(), y.save()
    monkeypatch.setattr(stories, "get_llm_client", fake_story_writer)
    monkeypatch.setattr(stories, "SpendGuard", lambda c, purpose="": c)
    client.force_login(user)
    client.post(reverse("admin:review_bulk"), {"action": "merge", "ids": [x.pk, y.pk]})
    st = Story.objects.get()
    assert (
        st.status == "draft"
        and st.kind == "briefing"
        and {s["article_id"] for s in st.sources} == {x.pk, y.pk}
    )


@pytest.mark.parametrize("case", ["one", "two_games", "same_outlet", "no_summary"])
def test_merge_refuses_bad_selections(two, case):
    a, b = two
    x = queued(a, 1)
    queued(a, 2)
    pick = {
        "one": [x],
        "two_games": [x, queued(b, 3)],
        "same_outlet": [x, queued(a, 4, url="https://outlet1.com/other")],
        "no_summary": [x, queued(a, 5, summary="")],
    }[case]
    with pytest.raises(ValueError):
        stories.merge_articles(pick, FakeLLMClient())


# ---------- roundups ----------
ROUNDUP = {
    "title": "Alpha Quest this week: a patch, a soundtrack and a trailer",
    "dek": "Three separate reports from different outlets, none of them a major announcement on its own.",
    "blocks": [
        {
            "text": "One outlet reports a small patch that addresses stability problems for some players. It reads as routine maintenance rather than a content update, and the report does not say who is affected or how long the problems had lasted before this fix arrived.",
            "sources": [0],
        },
        {
            "text": "A second report covers the soundtrack, naming some of the artists involved and saying a track list has been shared. It is background colour for fans and changes nothing about the game itself, so most readers can safely skim past it.",
            "sources": [1],
        },
        {
            "text": "A third outlet writes about a short trailer. It is described as brief and light on new information, so we treat it as a minor item rather than a headline development. Readers who want detail should open the linked reports.",
            "sources": [2, 0],
        },
    ],
    "key_points": ["A small stability patch", "Soundtrack details shared", "A brief trailer"],
    "tags": ["roundup"],
}


def leftovers(game):
    titles = [
        (
            "Stability patch released",
            "A small patch addresses stability problems for some players.",
        ),
        ("Soundtrack artists named", "The studio named some artists and shared a track list."),
        (
            "New short trailer appears",
            "A brief trailer appeared and offers little new information.",
        ),
    ]
    return [
        queued(game, i, summary=s).__class__.objects.filter(title=f"T{i}").update(title=t) or None
        for i, (t, s) in enumerate(titles, start=10)
    ]


def test_roundup_covers_leftovers_once_per_week(two):
    a, _ = two
    leftovers(a)
    fake = FakeLLMClient(lambda s, u: json.dumps(ROUNDUP))
    made = stories.build_for_game(a, fake)
    assert (
        len(made) == 1
        and made[0].kind == "roundup"
        and made[0].status == "draft"
        and len(made[0].sources) == 3
    )
    assert stories.build_roundup(a, fake) is None  # none left, and one already exists this week


def test_roundup_needs_enough_items_and_outlets(two):
    a, _ = two
    queued(a, 1), queued(a, 2)  # only two items
    assert stories.build_roundup(a, FakeLLMClient(lambda s, u: json.dumps(ROUNDUP))) is None
    queued(a, 3, url="https://o2.example.org/9")  # third item but the same outlet as #2
    Article.objects.filter(source_url__contains="o").update(source_url="https://same.example.org/z")
    assert stories.build_roundup(a, FakeLLMClient(lambda s, u: json.dumps(ROUNDUP))) is None


# ---------- API ----------
def test_feed_serialises_unassigned_articles_and_stories_expose_kind(client, db, user, two):
    a, _ = two
    queued(None, 1)
    feed = client.get("/api/v1/feed/").json()["results"]
    assert feed[0]["game_slug"] is None and feed[0]["game_name"] is None
    st = Story.objects.create(
        game=a,
        slug="s",
        title="Roundup title for the week",
        kind="roundup",
        status="published",
        published_at=timezone.now(),
        blocks=[{"text": "t", "sources": [0, 1]}],
        sources=[
            {"article_id": 1, "url": "https://a.example.com", "name": "a", "title": "t"},
            {"article_id": 2, "url": "https://b.example.org", "name": "b", "title": "t"},
        ],
        cluster_key="k",
    )
    lst = client.get("/api/v1/stories/").json()["results"]
    assert lst[0]["kind"] == "roundup" and st.slug == lst[0]["slug"]
    assert not mail.outbox and timedelta(0) == timedelta(0)


def test_reassign_games_command_fixes_stale_reasons(two):
    from django.core.management import call_command

    a, b = two
    stuck = art(a, None, title="Beta Racer 3 gets a patch", url="https://x.example.com/s1")
    kept = art(a, None, title="Hardware news roundup", url="https://x.example.com/s2")
    loose = art(None, None, title="Nothing to match here", url="https://x.example.com/s3")
    for x, why in (
        (stuck, "model assigned a different game (beta)"),
        (kept, "model could not assign a game"),
        (loose, "model could not assign a game"),
    ):
        Article.objects.filter(pk=x.pk).update(status="queued", review_reason=why)
    call_command("reassign_games", "--dry-run")
    stuck.refresh_from_db()
    assert stuck.game == a and "different game" in stuck.review_reason  # dry run changes nothing
    call_command("reassign_games")
    stuck.refresh_from_db()
    kept.refresh_from_db()
    loose.refresh_from_db()
    assert stuck.game == b and "moved to Beta Racer" in stuck.review_reason
    assert (
        kept.game == a
        and "kept from the source" in kept.review_reason
        and "could not assign" not in kept.review_reason
    )
    assert loose.game is None and "assign one" in loose.review_reason
