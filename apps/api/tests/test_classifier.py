import json

import pytest

from llm.classify import ClassificationFailed, ItemForLLM, classify, copies_source, parse_response
from llm.fake import FakeLLMClient

GAMES = {"test-game": "Test Game"}
ITEM = ItemForLLM(title="Patch 1.02 now live", lead="Version 1.02 is rolling out today with stability fixes", url="https://x.example.com/p", source_name="X")


def good(**over):
    d = {"game_slug": "test-game", "topic": "patch", "confidence": 0.93, "tags": ["Patch", " pc "],
         "summary": "A new update is going out to players that tightens stability and adds a graphics option.",
         "fact": {"kind": "patch", "platform": "pc", "patch_version": "1.02", "patch_date": "2026-11-02"}}
    d.update(over)
    return json.dumps(d)


def test_valid_output_parses_and_normalises_tags():
    c = classify(FakeLLMClient([good()]), ITEM, GAMES)
    assert c.topic == "patch" and c.tags == ["patch", "pc"] and c.fact.patch_version == "1.02"


def test_code_fences_are_tolerated():
    c = classify(FakeLLMClient(["```json\n" + good() + "\n```"]), ITEM, GAMES)
    assert c.game_slug == "test-game"


def test_invalid_then_valid_retries_once_with_error_feedback():
    fake = FakeLLMClient(["not json at all", good()])
    c = classify(fake, ITEM, GAMES)
    assert c.confidence == 0.93 and len(fake.calls) == 2
    assert "rejected" in fake.calls[1][1]


def test_invalid_twice_fails_for_review():
    with pytest.raises(ClassificationFailed):
        classify(FakeLLMClient(["{}", '{"topic":"x"}']), ITEM, GAMES)


@pytest.mark.parametrize("bad", [
    good(confidence=1.7), good(topic="gossip"), good(game_slug="other-game"), good(summary="too short"),
    good(fact={"kind": "release_date", "platform": "pc"}), good(fact={"kind": "requirement", "req_tier": "min"}),
])
def test_schema_violations_rejected(bad):
    with pytest.raises(ValueError):
        parse_response(bad, set(GAMES), "")


def test_summary_that_copies_source_is_rejected():
    copied = good(summary="Version 1.02 is rolling out today with stability fixes and more words follow here.")
    with pytest.raises(ValueError, match="copies"):
        parse_response(copied, set(GAMES), f"{ITEM.title} {ITEM.lead}")
    assert not copies_source("completely different original words here in this summary text okay", ITEM.lead)


def test_prompt_fences_untrusted_item():
    fake = FakeLLMClient([good()])
    classify(fake, ITEM, GAMES)
    system, user = fake.calls[0]
    assert "UNTRUSTED" in system and "<item>" in user and "</item>" in user
