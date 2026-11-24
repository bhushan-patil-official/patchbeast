from decimal import Decimal

import pytest

from llm.fake import FakeLLMClient
from llm.guard import SpendGuard, cost_usd
from llm.ports import LLMUnavailable
from modules.platform import services
from modules.platform.models import AlertEvent, LLMUsage, SiteSetting


def test_spend_guard_records_usage_and_enforces_daily_cap(db):
    s = SiteSetting.load()
    s.daily_llm_cap = Decimal("0.001")
    s.save()
    fake = FakeLLMClient(lambda sys, usr: "{}")
    guard = SpendGuard(fake)
    calls = 0
    with pytest.raises(LLMUnavailable):
        for _ in range(100):
            guard.complete("s" * 300, "u" * 300, max_tokens=700)
            calls += 1
    assert 0 < calls < 100 and len(fake.calls) == calls
    assert LLMUsage.objects.filter(ok=True).count() == calls
    spent, cap = services.spend_today()
    assert spent <= cap
    assert AlertEvent.objects.filter(kind="llm_spend_cap").count() == 1  # breach alerted once


def test_spend_guard_blocks_when_kill_switch_on(db):
    services.set_kill_switch(True)
    fake = FakeLLMClient(["{}"])
    with pytest.raises(LLMUnavailable, match="kill switch"):
        SpendGuard(fake).complete("s", "u")
    assert fake.calls == []


def test_failed_call_releases_reservation(db):
    from llm.ports import LLMRetryable

    guard = SpendGuard(FakeLLMClient([LLMRetryable("boom")]))
    with pytest.raises(LLMRetryable):
        guard.complete("s", "u")
    assert services.spend_today()[0] == Decimal("0")


def test_cost_math(settings):
    assert cost_usd(1_000_000, 1_000_000) == Decimal("0.6")  # 0.10 in + 0.50 out per MTok


def test_alert_cooldown_dedupes(db, mailoutbox):
    assert services.raise_alert("x", "first", dedupe_key="k")
    assert not services.raise_alert("x", "again", dedupe_key="k")
    assert len(mailoutbox) == 1 and AlertEvent.objects.count() == 1


def test_alert_survives_notifier_failure(db, monkeypatch):
    class Bad:
        name = "bad"

        def send(self, s, b):
            raise RuntimeError("smtp down")

    monkeypatch.setattr("modules.platform.services.get_notifiers", lambda: [Bad()])
    assert services.raise_alert("x", "msg")  # must not raise


def test_5xx_rate_alert(db, settings, mailoutbox):
    from modules.platform.tasks import check_alerts

    for _ in range(settings.PB["ALERT_5XX_THRESHOLD"]):
        services.count_5xx()
    check_alerts()
    assert any("server errors" in m.body for m in mailoutbox)


def test_healthz_ok_and_reports_kill_switch(client, db):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["ok"] and r.json()["kill_switch"] is False


def test_feature_flags_db_overrides_env(db):
    assert services.flag_enabled("ads") is False
    from modules.platform.models import FeatureFlag

    FeatureFlag.objects.create(key="ads", enabled=True)
    assert services.flag_enabled("ads") is True


def test_metrics_requires_token(client, settings, db):
    assert client.get("/metrics").status_code == 404
    settings.PB = {**settings.PB, "METRICS_TOKEN": "t"}
    assert client.get("/metrics", HTTP_AUTHORIZATION="Bearer t").status_code == 200


def test_revalidate_task_posts_secret(monkeypatch):
    import httpx

    from modules.platform.services import post_revalidation

    seen = {}

    def handler(req):
        seen["h"] = req.headers["x-revalidate-secret"]
        seen["body"] = req.content
        return httpx.Response(200, json={"ok": True})

    post_revalidation(["a"], ["/"], httpx.Client(transport=httpx.MockTransport(handler)))
    assert seen["h"] and b'"tags"' in seen["body"]
