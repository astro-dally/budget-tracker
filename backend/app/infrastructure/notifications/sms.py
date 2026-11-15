"""SMS notification channel (stub)."""

from __future__ import annotations

import logging

from app.application.ports import NotificationChannel
from app.domain.alert import Alert

logger = logging.getLogger(__name__)

SMS_MAX_LENGTH = 160


class SmsChannel(NotificationChannel):
    """Stub SMS gateway: formats a 160-character message and logs it.

    A real provider (Twilio, MSG91...) would be a drop-in replacement class.
    """

    name = "sms"

    def __init__(self, phone_number: str | None) -> None:
        self._phone_number = phone_number

    @staticmethod
    def format(alert: Alert) -> str:
        """Shorten the alert to fit one SMS."""
        text = f"Budget alert: {alert.message}"
        return text if len(text) <= SMS_MAX_LENGTH else text[: SMS_MAX_LENGTH - 1] + "…"

    def send(self, alert: Alert) -> None:
        if self._phone_number is None:
            logger.debug("SMS channel has no phone number configured; skipping")
            return
        logger.info("SMS (stub) to %s: %s", self._phone_number, self.format(alert))
