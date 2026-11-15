"""System clock adapter for the :class:`~app.application.ports.Clock` port."""

from datetime import UTC, date, datetime


class SystemClock:
    """Real time. Tests inject a fixed clock instead."""

    def today(self) -> date:
        """Today's local date."""
        return date.today()

    def now(self) -> datetime:
        """The current UTC timestamp."""
        return datetime.now(UTC)
