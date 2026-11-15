"""Console notification channel."""

from __future__ import annotations

import sys
from typing import TextIO

from app.application.ports import NotificationChannel
from app.domain.alert import Alert


class ConsoleChannel(NotificationChannel):
    """Prints alerts to a text stream (stdout by default); handy during development."""

    name = "console"

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def send(self, alert: Alert) -> None:
        self._stream.write(f"[ALERT:{alert.level.value.upper()}] {alert.message}\n")
        self._stream.flush()
