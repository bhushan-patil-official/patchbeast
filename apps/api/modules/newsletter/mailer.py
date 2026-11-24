"""Mailer port + adapters."""

from typing import Protocol

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class Mailer(Protocol):
    def send(self, to: str, subject: str, text: str, html: str | None = None, headers: dict | None = None) -> None: ...


class DjangoMailer:
    def send(self, to, subject, text, html=None, headers=None):
        m = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to], headers=headers or {})
        if html:
            m.attach_alternative(html, "text/html")
        m.send(fail_silently=False)


class MemoryMailer:
    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to, subject, text, html=None, headers=None):
        self.sent.append({"to": to, "subject": subject, "text": text, "html": html, "headers": headers or {}})


def get_mailer() -> Mailer:
    return DjangoMailer()
