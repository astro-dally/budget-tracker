"""SQLAlchemy adapter for :class:`~app.application.ports.TransactionRepository` (owner-scoped)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import ColumnElement, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.application.queries import Page, SortDirection, SortField, TransactionQuery
from app.domain.enums import CategorySource, TransactionType
from app.domain.errors import DuplicateRecurrenceError, NotFoundError
from app.domain.money import Money, Period
from app.domain.transaction import Transaction, normalize_description
from app.infrastructure.persistence.models import TransactionRow

_SORT_COLUMNS: dict[SortField, Any] = {
    SortField.OCCURRED_ON: TransactionRow.occurred_on,
    SortField.AMOUNT: TransactionRow.amount_minor,
    SortField.DESCRIPTION: TransactionRow.description_key,
}


def _to_domain(row: TransactionRow) -> Transaction:
    return Transaction(
        id=row.id,
        type=TransactionType(row.type),
        amount=Money.from_minor_units(row.amount_minor),
        description=row.description,
        occurred_on=row.occurred_on,
        category_id=row.category_id,
        category_source=CategorySource(row.category_source),
        recurring_id=row.recurring_id,
    )


def _copy(transaction: Transaction, row: TransactionRow) -> None:
    row.type = transaction.type.value
    row.amount_minor = transaction.amount.to_minor_units()
    row.description = transaction.description
    row.description_key = normalize_description(transaction.description)
    row.occurred_on = transaction.occurred_on
    row.category_id = transaction.category_id
    row.category_source = transaction.category_source.value
    row.recurring_id = transaction.recurring_id


def _filters(owner_id: str, query: TransactionQuery) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [TransactionRow.owner_id == owner_id]
    if query.type is not None:
        conditions.append(TransactionRow.type == query.type.value)
    if query.category_id is not None:
        conditions.append(TransactionRow.category_id == query.category_id)
    if query.search:
        term = normalize_description(query.search)
        conditions.append(TransactionRow.description_key.contains(term, autoescape=True))
    if query.date_from is not None:
        conditions.append(TransactionRow.occurred_on >= query.date_from)
    if query.date_to is not None:
        conditions.append(TransactionRow.occurred_on <= query.date_to)
    return conditions


class SqlAlchemyTransactionRepository:
    """Stores one user's transactions and answers the aggregate queries services need."""

    def __init__(self, sessions: sessionmaker[Session], owner_id: str) -> None:
        self._sessions = sessions
        self._owner_id = owner_id
        self._is_mine = TransactionRow.owner_id == owner_id

    def _mine(self, session: Session, transaction_id: str) -> TransactionRow | None:
        return session.scalar(
            select(TransactionRow).where(TransactionRow.id == transaction_id, self._is_mine)
        )

    def add(self, transaction: Transaction) -> None:
        row = TransactionRow(id=transaction.id, owner_id=self._owner_id)
        _copy(transaction, row)
        try:
            with self._sessions.begin() as session:
                session.add(row)
        except IntegrityError as exc:
            if transaction.recurring_id is not None and self.exists_for_recurrence(
                transaction.recurring_id, transaction.occurred_on
            ):
                raise DuplicateRecurrenceError(
                    f"Occurrence {transaction.occurred_on} already generated"
                ) from exc
            raise

    def update(self, transaction: Transaction) -> None:
        with self._sessions.begin() as session:
            row = self._mine(session, transaction.id)
            if row is None:
                raise NotFoundError("Transaction", transaction.id)
            _copy(transaction, row)

    def delete(self, transaction_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(TransactionRow).where(TransactionRow.id == transaction_id, self._is_mine)
            )

    def get(self, transaction_id: str) -> Transaction | None:
        with self._sessions() as session:
            row = self._mine(session, transaction_id)
            return _to_domain(row) if row else None

    def search(self, query: TransactionQuery) -> Page[Transaction]:
        conditions = _filters(self._owner_id, query)
        column = _SORT_COLUMNS[query.sort_by]
        order = column.asc() if query.sort_direction is SortDirection.ASC else column.desc()
        with self._sessions() as session:
            total = session.scalar(
                select(func.count()).select_from(TransactionRow).where(*conditions)
            )
            rows = session.scalars(
                select(TransactionRow)
                .where(*conditions)
                .order_by(order, TransactionRow.created_at.desc(), TransactionRow.id)
                .offset(query.offset)
                .limit(query.page_size)
            )
            items = [_to_domain(row) for row in rows]
        return Page(items=items, total=total or 0, page=query.page, page_size=query.page_size)

    def list_between(self, start: date, end: date) -> list[Transaction]:
        with self._sessions() as session:
            rows = session.scalars(
                select(TransactionRow)
                .where(self._is_mine, TransactionRow.occurred_on.between(start, end))
                .order_by(TransactionRow.occurred_on, TransactionRow.created_at)
            )
            return [_to_domain(row) for row in rows]

    def recent(self, limit: int) -> list[Transaction]:
        with self._sessions() as session:
            rows = session.scalars(
                select(TransactionRow)
                .where(self._is_mine)
                .order_by(TransactionRow.occurred_on.desc(), TransactionRow.created_at.desc())
                .limit(limit)
            )
            return [_to_domain(row) for row in rows]

    def expense_total(self, category_id: str, period: Period) -> Money:
        with self._sessions() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(TransactionRow.amount_minor), 0)).where(
                    self._is_mine,
                    TransactionRow.category_id == category_id,
                    TransactionRow.type == TransactionType.EXPENSE.value,
                    TransactionRow.occurred_on.between(period.start, period.end),
                )
            )
        return Money.from_minor_units(int(total or 0))

    def exists_for_recurrence(self, recurring_id: str, occurred_on: date) -> bool:
        with self._sessions() as session:
            found = session.scalar(
                select(TransactionRow.id).where(
                    self._is_mine,
                    TransactionRow.recurring_id == recurring_id,
                    TransactionRow.occurred_on == occurred_on,
                )
            )
        return found is not None

    def latest_manual_category_for(self, normalized_description: str) -> str | None:
        with self._sessions() as session:
            return session.scalar(
                select(TransactionRow.category_id)
                .where(
                    self._is_mine,
                    TransactionRow.description_key == normalized_description,
                    TransactionRow.category_source == CategorySource.MANUAL.value,
                    TransactionRow.category_id.is_not(None),
                )
                .order_by(TransactionRow.occurred_on.desc(), TransactionRow.created_at.desc())
                .limit(1)
            )

    def reassign_category(self, from_category_id: str, to_category_id: str) -> int:
        with self._sessions.begin() as session:
            moved = session.scalar(
                select(func.count())
                .select_from(TransactionRow)
                .where(self._is_mine, TransactionRow.category_id == from_category_id)
            )
            session.execute(
                update(TransactionRow)
                .where(self._is_mine, TransactionRow.category_id == from_category_id)
                .values(category_id=to_category_id)
            )
        return moved or 0

    def count(self) -> int:
        with self._sessions() as session:
            return (
                session.scalar(
                    select(func.count()).select_from(TransactionRow).where(self._is_mine)
                )
                or 0
            )
