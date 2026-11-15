"""Recurring payments: the :class:`RecurrenceSchedule` value object and the
:class:`RecurringPayment` entity (Single Responsibility: *when* money repeats).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, replace
from datetime import date, timedelta

from app.domain.enums import Frequency, TransactionType
from app.domain.errors import DomainValidationError
from app.domain.ids import new_id
from app.domain.money import Money


@dataclass(frozen=True, slots=True)
class RecurrenceSchedule:
    """Computes occurrence dates for a daily, weekly or monthly schedule.

    Monthly schedules stay anchored to the start day and clamp to short
    months: a schedule starting on 31 Jan yields 29 Feb (leap year), 31 Mar,
    30 Apr... It never drifts to the 28th permanently.
    """

    frequency: Frequency
    start_date: date
    end_date: date | None = None

    def __post_init__(self) -> None:
        if self.end_date is not None and self.end_date < self.start_date:
            raise DomainValidationError("End date must not be before the start date")

    def nth(self, index: int) -> date:
        """Return the ``index``-th occurrence (0 = start date)."""
        if self.frequency is Frequency.DAILY:
            return self.start_date + timedelta(days=index)
        if self.frequency is Frequency.WEEKLY:
            return self.start_date + timedelta(weeks=index)
        months = self.start_date.month - 1 + index
        year = self.start_date.year + months // 12
        month = months % 12 + 1
        day = min(self.start_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def _first_index_after(self, after: date | None) -> int:
        if after is None or after < self.start_date:
            return 0
        if self.frequency is Frequency.DAILY:
            return (after - self.start_date).days + 1
        if self.frequency is Frequency.WEEKLY:
            return (after - self.start_date).days // 7 + 1
        index = (after.year - self.start_date.year) * 12 + after.month - self.start_date.month
        while self.nth(index) <= after:
            index += 1
        return index

    def occurrences_between(self, after: date | None, until: date) -> list[date]:
        """Occurrences strictly after ``after`` (or from the start) up to ``until`` inclusive."""
        dates: list[date] = []
        index = self._first_index_after(after)
        while True:
            occurrence = self.nth(index)
            if occurrence > until or (self.end_date and occurrence > self.end_date):
                return dates
            dates.append(occurrence)
            index += 1

    def next_on_or_after(self, day: date) -> date | None:
        """The first occurrence on or after ``day``, or None when the schedule has ended."""
        occurrence = self.nth(self._first_index_after(day - timedelta(days=1)))
        if self.end_date is not None and occurrence > self.end_date:
            return None
        return occurrence


@dataclass(frozen=True, slots=True)
class RecurringPayment:
    """A payment that repeats on a schedule, such as rent, a subscription or an EMI.

    ``last_generated_on`` records how far transactions have been materialised.
    Generation is idempotent: the generator asks for dates *after* this mark,
    and the store's unique ``(recurring_id, occurred_on)`` constraint rejects
    any duplicate if a crash happened between generating and saving the mark.
    """

    id: str
    description: str
    amount: Money
    type: TransactionType
    schedule: RecurrenceSchedule
    category_id: str | None = None
    is_active: bool = True
    last_generated_on: date | None = None

    def __post_init__(self) -> None:
        if not self.amount.is_positive():
            raise DomainValidationError("Recurring amount must be greater than zero")
        cleaned = " ".join(self.description.split())
        if not cleaned:
            raise DomainValidationError("Description must not be empty")
        object.__setattr__(self, "description", cleaned)

    @classmethod
    def create(
        cls,
        *,
        description: str,
        amount: Money,
        type: TransactionType,
        schedule: RecurrenceSchedule,
        category_id: str | None,
    ) -> RecurringPayment:
        """Factory method that assigns a fresh id."""
        return cls(
            id=new_id(),
            description=description,
            amount=amount,
            type=type,
            schedule=schedule,
            category_id=category_id,
        )

    def due_occurrences(self, today: date) -> list[date]:
        """Dates that should have a transaction by ``today`` but have not been generated yet."""
        if not self.is_active:
            return []
        return self.schedule.occurrences_between(self.last_generated_on, today)

    def next_due(self, today: date) -> date | None:
        """The next upcoming occurrence (today counts if not yet generated)."""
        if not self.is_active:
            return None
        start = today
        if self.last_generated_on is not None and self.last_generated_on >= today:
            start = self.last_generated_on + timedelta(days=1)
        return self.schedule.next_on_or_after(start)

    def generated_through(self, day: date) -> RecurringPayment:
        """Return a copy whose generation mark has advanced to ``day``."""
        return replace(self, last_generated_on=day)

    def paused(self) -> RecurringPayment:
        """Return a paused copy; no transactions are generated while paused."""
        return replace(self, is_active=False)

    def resumed(self, today: date) -> RecurringPayment:
        """Return an active copy that does not back-fill dates missed while paused."""
        mark = max(self.last_generated_on or date.min, today - timedelta(days=1))
        return replace(self, is_active=True, last_generated_on=mark)
