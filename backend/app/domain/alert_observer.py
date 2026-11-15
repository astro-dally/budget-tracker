"""Observer pattern: the observer interface.

``AlertObserver`` is the *Observer*; the *Subject* is
:class:`app.application.budget_monitor.BudgetMonitor`, which calls
:meth:`AlertObserver.on_alert` for every alert it raises. The subject knows
observers only through this interface, so delivery mechanisms (notification
fan-out, analytics, audit logging...) can be added without touching it.
"""

from abc import ABC, abstractmethod

from app.domain.alert import Alert


class AlertObserver(ABC):
    """Receives alerts from a subject."""

    @abstractmethod
    def on_alert(self, alert: Alert) -> None:
        """React to a newly raised alert."""
