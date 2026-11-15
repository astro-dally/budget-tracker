"""Concrete observers attached to :class:`~app.application.budget_monitor.BudgetMonitor`."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from app.application.ports import NotificationChannel
from app.domain.alert import Alert
from app.domain.alert_observer import AlertObserver

logger = logging.getLogger(__name__)


class NotificationDispatcher(AlertObserver):
    """Concrete observer that fans an alert out to every notification channel.

    A failing channel (e.g. an SMTP outage) is logged and skipped, so it can
    never stop the other channels or the request that triggered the alert.
    """

    def __init__(self, channels: Sequence[NotificationChannel]) -> None:
        self._channels = tuple(channels)

    @property
    def channel_names(self) -> list[str]:
        """Names of the configured channels."""
        return [channel.name for channel in self._channels]

    def on_alert(self, alert: Alert) -> None:
        for channel in self._channels:
            try:
                channel.send(alert)
            except Exception:
                logger.exception("Notification channel '%s' failed", channel.name)
