"""Double opt-in newsletter + weekly digest of CONFIRMED changes."""

from datetime import timedelta
from html import escape

from django.conf import settings
from django.utils import timezone

from modules.content import selectors as content_selectors
from modules.platform.services import flag_enabled

from .mailer import Mailer, get_mailer
from .models import DigestRun, Subscriber

RESEND_AFTER = timedelta(minutes=10)


class NewsletterDisabled(Exception):
    pass


def _links(sub: Subscriber) -> tuple[str, str]:
    site = settings.SITE_URL
    return (
        f"{site}/newsletter/confirm?token={sub.confirm_token}",
        f"{site}/api/v1/newsletter/unsubscribe/?token={sub.unsub_token}",
    )


def subscribe(email: str, *, source: str = "", mailer: Mailer | None = None) -> None:
    """Always returns silently (no account enumeration). Sends a confirmation mail when needed."""
    if not flag_enabled("newsletter"):
        raise NewsletterDisabled
    email = email.strip().lower()
    sub, created = Subscriber.objects.get_or_create(
        email=email, defaults={"signup_source": source[:60]}
    )
    if sub.active:
        return
    if sub.unsubscribed_at and not created:
        sub.unsubscribed_at = None  # re-subscribing requires a fresh confirmation
        sub.confirmed = False
    if (
        sub.confirmation_sent_at
        and timezone.now() - sub.confirmation_sent_at < RESEND_AFTER
        and not created
    ):
        return
    confirm_url, _ = _links(sub)
    (mailer or get_mailer()).send(
        email,
        "Confirm your Patchbeast subscription",
        f"Confirm your subscription to the Patchbeast weekly digest:\n{confirm_url}\n\nIf you did not ask for this, ignore this email; nothing will be sent.",
        f'<p>Confirm your subscription to the Patchbeast weekly digest:</p><p><a href="{escape(confirm_url)}">Confirm subscription</a></p>'
        "<p>If you did not ask for this, ignore this email; nothing will be sent.</p>",
    )
    sub.confirmation_sent_at = timezone.now()
    sub.save()


def confirm(token: str) -> bool:
    sub = Subscriber.objects.filter(confirm_token=token).first()
    if not sub:
        return False
    if not sub.confirmed:
        sub.confirmed, sub.confirmed_at, sub.unsubscribed_at = True, timezone.now(), None
        sub.save()
    return True


def unsubscribe(token: str) -> bool:
    sub = Subscriber.objects.filter(unsub_token=token).first()
    if not sub:
        return False
    if sub.unsubscribed_at is None:
        sub.unsubscribed_at = timezone.now()
        sub.save()
    return True


def iso_week(dt=None) -> str:
    y, w, _ = (dt or timezone.now()).isocalendar()
    return f"{y}-W{w:02d}"


def build_digest(since=None) -> tuple[str, str, int]:
    changes = list(content_selectors.weekly_changes(since))
    lines, html = ["Confirmed changes this week (each links to its source):", ""], [
        "<h2>Confirmed changes this week</h2>"
    ]
    by_game: dict[str, list] = {}
    for c in changes:
        by_game.setdefault(c.game.name, []).append(c)
    for game, items in by_game.items():
        lines.append(game)
        html.append(f"<h3>{escape(game)}</h3><ul>")
        for c in items:
            lines.append(
                f"  - {c.title}"
                + (f" — {c.detail}" if c.detail else "")
                + (f"\n    source: {c.source_url}" if c.source_url else "")
            )
            link = f' (<a href="{escape(c.source_url)}">source</a>)' if c.source_url else ""
            html.append(
                f"<li><strong>{escape(c.title)}</strong>{' — ' + escape(c.detail) if c.detail else ''}{link}</li>"
            )
        html.append("</ul>")
        lines.append("")
    return "\n".join(lines), "".join(html), len(changes)


def send_digest_to(
    sub: Subscriber, week: str, text: str, html: str, mailer: Mailer | None = None
) -> bool:
    if not sub.active or sub.last_digest_week == week:
        return False
    _, unsub = _links(sub)
    (mailer or get_mailer()).send(
        sub.email, f"Patchbeast weekly digest · {week}",
        f"{text}\nUnsubscribe: {unsub}\n",
        f'{html}<hr><p style="font-size:12px"><a href="{escape(unsub)}">Unsubscribe</a> · Patchbeast is a tracker; every item links to its source.</p>',
        headers={"List-Unsubscribe": f"<{settings.SITE_URL}/api/v1/newsletter/unsubscribe/?token={sub.unsub_token}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"},
    )  # fmt: skip
    sub.last_digest_week = week
    sub.save(update_fields=["last_digest_week", "updated_at"])
    return True


def start_weekly_digest() -> tuple[DigestRun | None, list[int]]:
    """Idempotent per ISO week: returns (run, subscriber ids to mail). Empty weeks send nothing."""
    if not flag_enabled("newsletter"):
        return None, []
    week = iso_week()
    run, created = DigestRun.objects.get_or_create(iso_week=week)
    if not created:
        return run, []
    _, _, count = build_digest()
    run.item_count = count
    ids = (
        list(
            Subscriber.objects.filter(confirmed=True, unsubscribed_at__isnull=True).values_list(
                "id", flat=True
            )
        )
        if count
        else []
    )
    run.recipients = len(ids)
    run.save()
    return run, ids
