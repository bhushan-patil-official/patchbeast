from django.core import mail

from modules.content import services as c
from modules.newsletter import services
from modules.newsletter.models import Subscriber
from modules.platform.models import FeatureFlag


def test_double_opt_in_flow(client, db):
    r = client.post(
        "/api/v1/newsletter/subscribe/",
        {"email": "Fan@Example.com"},
        content_type="application/json",
    )
    assert r.status_code == 200
    sub = Subscriber.objects.get(email="fan@example.com")
    assert (
        not sub.confirmed
        and "/newsletter/confirm?token=" + sub.confirm_token in mail.outbox[0].body
    )
    assert services.iso_week()  # smoke
    assert (
        client.post(
            "/api/v1/newsletter/confirm/", {"token": "bad"}, content_type="application/json"
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/newsletter/confirm/",
            {"token": sub.confirm_token},
            content_type="application/json",
        ).status_code
        == 200
    )
    sub.refresh_from_db()
    assert sub.confirmed and sub.active


def test_unconfirmed_never_receives_digest(db, game):
    Subscriber.objects.create(email="u@example.com")
    c.record_change(game, "patch", "P", verification="confirmed")
    run, ids = services.start_weekly_digest()
    assert ids == []


def test_honeypot_and_invalid_email(client, db):
    assert (
        client.post(
            "/api/v1/newsletter/subscribe/",
            {"email": "bot@example.com", "website": "x"},
            content_type="application/json",
        ).status_code
        == 200
    )
    assert not Subscriber.objects.exists()
    assert (
        client.post(
            "/api/v1/newsletter/subscribe/", {"email": "nope"}, content_type="application/json"
        ).status_code
        == 400
    )


def test_digest_only_confirmed_changes_idempotent_with_unsubscribe(db, game):
    s = Subscriber.objects.create(email="a@example.com", confirmed=True)
    c.record_change(
        game,
        "patch",
        "Confirmed patch",
        source_url="https://src.example.com/p",
        verification="confirmed",
    )
    c.record_change(game, "news", "Just reported", verification="reported")
    run, ids = services.start_weekly_digest()
    assert ids == [s.pk] and run.item_count == 1
    text, html, n = services.build_digest()
    assert (
        "Confirmed patch" in text
        and "Just reported" not in text
        and "https://src.example.com/p" in text
    )
    assert services.send_digest_to(s, run.iso_week, text, html)
    msg = mail.outbox[-1]
    assert (
        "Unsubscribe" in msg.body
        and msg.extra_headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    )
    assert not services.send_digest_to(s, run.iso_week, text, html)  # once per week
    assert services.start_weekly_digest()[1] == []  # run is idempotent per ISO week


def test_empty_week_sends_nothing(db):
    Subscriber.objects.create(email="a@example.com", confirmed=True)
    assert services.start_weekly_digest()[1] == []


def test_unsubscribe_and_resubscribe_needs_confirmation(client, db):
    s = Subscriber.objects.create(email="a@example.com", confirmed=True)
    assert (
        client.post(
            "/api/v1/newsletter/unsubscribe/",
            {"token": s.unsub_token},
            content_type="application/json",
        ).status_code
        == 200
    )
    s.refresh_from_db()
    assert not s.active
    services.subscribe("a@example.com")
    s.refresh_from_db()
    assert not s.confirmed


def test_flag_off_disables_signup(client, db):
    FeatureFlag.objects.create(key="newsletter", enabled=False)
    assert (
        client.post(
            "/api/v1/newsletter/subscribe/",
            {"email": "a@example.com"},
            content_type="application/json",
        ).status_code
        == 404
    )
