"""Notifier port + adapters (email, Telegram, log)."""

import logging
from typing import Protocol

import httpx
from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


class Notifier(Protocol):
    name: str

    def send(self, subject: str, body: str) -> None: ...


class LogNotifier:
    name = "log"

    def send(self, subject: str, body: str) -> None:
        log.error("ALERT %s: %s", subject, body)


class EmailNotifier:
    name = "email"

    def __init__(self, to: str):
        self.to = to

    def send(self, subject: str, body: str) -> None:
        send_mail(f"[Patchbeast] {subject}", body, None, [self.to], fail_silently=False)


class TelegramNotifier:
    name = "telegram"

    def __init__(self, token: str, chat_id: str, client: httpx.Client | None = None):
        self.token, self.chat_id, self.client = token, chat_id, client

    def send(self, subject: str, body: str) -> None:
        client = self.client or httpx.Client(timeout=10)
        r = client.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": f"*{subject}*\n{body}"[:4000],
                "parse_mode": "Markdown",
            },
        )
        r.raise_for_status()


def get_notifiers() -> list[Notifier]:
    cfg = settings.PB
    out: list[Notifier] = [LogNotifier()]
    if cfg["ALERT_EMAIL_TO"]:
        out.append(EmailNotifier(cfg["ALERT_EMAIL_TO"]))
    if cfg["TELEGRAM_BOT_TOKEN"] and cfg["TELEGRAM_CHAT_ID"]:
        out.append(TelegramNotifier(cfg["TELEGRAM_BOT_TOKEN"], cfg["TELEGRAM_CHAT_ID"]))
    return out
