"""Owner-scoped SQLAlchemy adapter for the ``RecurringPaymentRepository`` port."""

from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.domain.enums import Frequency, TransactionType
from app.domain.errors import NotFoundError
from app.domain.money import Money
from app.domain.recurrence import RecurrenceSchedule, RecurringPayment
from app.infrastructure.persistence.models import RecurringPaymentRow


def _to_domain(row: RecurringPaymentRow) -> RecurringPayment:
    return RecurringPayment(
        id=row.id,
        description=row.description,
        amount=Money.from_minor_units(row.amount_minor),
        type=TransactionType(row.type),
        schedule=RecurrenceSchedule(Frequency(row.frequency), row.start_date, row.end_date),
        category_id=row.category_id,
        is_active=row.is_active,
        last_generated_on=row.last_generated_on,
    )


def _copy(payment: RecurringPayment, row: RecurringPaymentRow) -> None:
    row.description = payment.description
    row.amount_minor = payment.amount.to_minor_units()
    row.type = payment.type.value
    row.category_id = payment.category_id
    row.frequency = payment.schedule.frequency.value
    row.start_date = payment.schedule.start_date
    row.end_date = payment.schedule.end_date
    row.is_active = payment.is_active
    row.last_generated_on = payment.last_generated_on


class SqlAlchemyRecurringPaymentRepository:
    """Stores one user's recurring payments."""

    def __init__(self, sessions: sessionmaker[Session], owner_id: str) -> None:
        self._sessions = sessions
        self._owner_id = owner_id

    def _mine(self, session: Session, recurring_id: str) -> RecurringPaymentRow | None:
        return session.scalar(
            select(RecurringPaymentRow).where(
                RecurringPaymentRow.id == recurring_id,
                RecurringPaymentRow.owner_id == self._owner_id,
            )
        )

    def add(self, payment: RecurringPayment) -> None:
        row = RecurringPaymentRow(id=payment.id, owner_id=self._owner_id)
        _copy(payment, row)
        with self._sessions.begin() as session:
            session.add(row)

    def update(self, payment: RecurringPayment) -> None:
        with self._sessions.begin() as session:
            row = self._mine(session, payment.id)
            if row is None:
                raise NotFoundError("Recurring payment", payment.id)
            _copy(payment, row)

    def mark_generated(self, recurring_id: str, through: date) -> None:
        with self._sessions.begin() as session:
            session.execute(
                update(RecurringPaymentRow)
                .where(
                    RecurringPaymentRow.id == recurring_id,
                    RecurringPaymentRow.owner_id == self._owner_id,
                )
                .values(last_generated_on=through)
            )

    def delete(self, recurring_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(RecurringPaymentRow).where(
                    RecurringPaymentRow.id == recurring_id,
                    RecurringPaymentRow.owner_id == self._owner_id,
                )
            )

    def get(self, recurring_id: str) -> RecurringPayment | None:
        with self._sessions() as session:
            row = self._mine(session, recurring_id)
            return _to_domain(row) if row else None

    def list_all(self) -> list[RecurringPayment]:
        with self._sessions() as session:
            return [
                _to_domain(row)
                for row in session.scalars(
                    select(RecurringPaymentRow).where(
                        RecurringPaymentRow.owner_id == self._owner_id
                    )
                )
            ]

    def reassign_category(self, from_category_id: str, to_category_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                update(RecurringPaymentRow)
                .where(
                    RecurringPaymentRow.owner_id == self._owner_id,
                    RecurringPaymentRow.category_id == from_category_id,
                )
                .values(category_id=to_category_id)
            )
