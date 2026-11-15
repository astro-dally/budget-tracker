"""Use cases: read and acknowledge alert history."""

from __future__ import annotations

from app.application.ports import AlertRepository
from app.domain.alert import Alert
from app.domain.errors import NotFoundError


class AlertService:
    """Lists alerts and marks them as read."""

    def __init__(self, alerts: AlertRepository) -> None:
        self._alerts = alerts

    def list_all(self, limit: int = 50, unread_only: bool = False) -> list[Alert]:
        """Newest alerts first."""
        return self._alerts.list_recent(limit, unread_only)

    def unread_count(self) -> int:
        """Number of unread alerts (the bell badge)."""
        return self._alerts.unread_count()

    def mark_read(self, alert_id: str) -> None:
        """Mark one alert as read."""
        if not self._alerts.mark_read(alert_id):
            raise NotFoundError("Alert", alert_id)

    def mark_all_read(self) -> int:
        """Mark every alert as read."""
        return self._alerts.mark_all_read()
