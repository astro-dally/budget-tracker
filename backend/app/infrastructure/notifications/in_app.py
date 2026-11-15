"""In-app notification channel that pushes alerts to the browser via SSE."""

from __future__ import annotations

from typing import Protocol

from app.application.ports import NotificationChannel
from app.domain.alert import Alert


class AlertPublisher(Protocol):
    """Anything that can broadcast an alert to connected clients."""

    def publish(self, user_id: str, alert: Alert) -> None:
        """Broadcast the alert to one user's connections."""
        ...


class InAppChannel(NotificationChannel):
    """Publishes alerts to the SSE hub; the UI shows a toast and bumps the bell badge."""

    name = "in_app"

    def __init__(self, publisher: AlertPublisher, user_id: str) -> None:
        self._publisher = publisher
        self._user_id = user_id

    def send(self, alert: Alert) -> None:
        self._publisher.publish(self._user_id, alert)
