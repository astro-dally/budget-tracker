"""Use cases: manage recurring payments and generate their transactions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from app.application.ports import CategoryRepository, Clock, RecurringPaymentRepository
from app.application.transaction_service import TransactionService
from app.domain.enums import Frequency, TransactionType
from app.domain.errors import NotFoundError
from app.domain.money import Money
from app.domain.recurrence import RecurrenceSchedule, RecurringPayment

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RecurringInput:
    """Data for creating a recurring payment."""

    description: str
    amount: Money
    type: TransactionType
    frequency: Frequency
    start_date: date
    end_date: date | None = None
    category_id: str | None = None


@dataclass(frozen=True, slots=True)
class UpcomingPayment:
    """A recurring payment and the date it is next due."""

    payment: RecurringPayment
    due_on: date


class RecurringService:
    """Manages recurring payments and materialises due occurrences idempotently."""

    def __init__(
        self,
        recurring: RecurringPaymentRepository,
        categories: CategoryRepository,
        transactions: TransactionService,
        clock: Clock,
    ) -> None:
        self._recurring = recurring
        self._categories = categories
        self._transactions = transactions
        self._clock = clock

    def list_all(self) -> list[RecurringPayment]:
        """All recurring payments, active first, then by description."""
        return sorted(
            self._recurring.list_all(), key=lambda p: (not p.is_active, p.description.lower())
        )

    def get(self, recurring_id: str) -> RecurringPayment:
        """Fetch one recurring payment or raise :class:`NotFoundError`."""
        payment = self._recurring.get(recurring_id)
        if payment is None:
            raise NotFoundError("Recurring payment", recurring_id)
        return payment

    def create(self, data: RecurringInput) -> RecurringPayment:
        """Create a recurring payment and immediately generate anything already due."""
        if data.category_id is not None and self._categories.get(data.category_id) is None:
            raise NotFoundError("Category", data.category_id)
        payment = RecurringPayment.create(
            description=data.description,
            amount=data.amount,
            type=data.type,
            schedule=RecurrenceSchedule(data.frequency, data.start_date, data.end_date),
            category_id=data.category_id,
        )
        self._recurring.add(payment)
        self._generate(payment)
        return self.get(payment.id)

    def pause(self, recurring_id: str) -> RecurringPayment:
        """Stop generating transactions."""
        payment = self.get(recurring_id).paused()
        self._recurring.update(payment)
        return payment

    def resume(self, recurring_id: str) -> RecurringPayment:
        """Start generating again from today (dates missed while paused are skipped)."""
        payment = self.get(recurring_id).resumed(self._clock.today())
        self._recurring.update(payment)
        self._generate(payment)
        return self.get(recurring_id)

    def delete(self, recurring_id: str) -> None:
        """Delete a recurring payment; transactions it already generated are kept."""
        self.get(recurring_id)
        self._recurring.delete(recurring_id)

    def generate_due(self) -> int:
        """Generate every due occurrence of every active payment; return how many were created.

        Safe to run repeatedly, concurrently or after a restart (idempotent).
        """
        created = sum(self._generate(p) for p in self._recurring.list_all() if p.is_active)
        if created:
            logger.info("Generated %d recurring transaction(s)", created)
        return created

    def upcoming(self, limit: int) -> list[UpcomingPayment]:
        """The next due date of each active payment, soonest first."""
        today = self._clock.today()
        upcoming = [
            UpcomingPayment(payment, due)
            for payment in self._recurring.list_all()
            if (due := payment.next_due(today)) is not None
        ]
        return sorted(upcoming, key=lambda item: item.due_on)[:limit]

    def _generate(self, payment: RecurringPayment) -> int:
        today = self._clock.today()
        created = sum(
            self._transactions.record_recurring(payment, day)
            for day in payment.due_occurrences(today)
        )
        if payment.is_active and (
            payment.last_generated_on is None or payment.last_generated_on < today
        ):
            self._recurring.mark_generated(payment.id, today)
        return created
