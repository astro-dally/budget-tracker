"""E-mail notification channel (SMTP when configured, logged stub otherwise)."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.application.ports import NotificationChannel
from app.domain.alert import Alert

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EmailSettings:
    """SMTP configuration. With ``host=None`` the channel only logs (stub mode)."""

    sender: str
    recipient: str
    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    use_tls: bool = True


class EmailChannel(NotificationChannel):
    """Sends alerts by e-mail through SMTP."""

    name = "email"

    def __init__(self, settings: EmailSettings) -> None:
        self._settings = settings

    def build_message(self, alert: Alert) -> EmailMessage:
        """Compose the e-mail for an alert."""
        message = EmailMessage()
        message["Subject"] = f"Budget alert: {alert.category_name} ({alert.period})"
        message["From"] = self._settings.sender
        message["To"] = self._settings.recipient
        message.set_content(alert.message)
        return message

    def send(self, alert: Alert) -> None:
        message = self.build_message(alert)
        if self._settings.host is None:
            logger.info("Email (stub) to %s: %s", self._settings.recipient, alert.message)
            return
        with smtplib.SMTP(self._settings.host, self._settings.port, timeout=10) as smtp:
            if self._settings.use_tls:
                smtp.starttls()
            if self._settings.username and self._settings.password:
                smtp.login(self._settings.username, self._settings.password)
            smtp.send_message(message)
