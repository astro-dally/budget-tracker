"""Cross-user, read-only statistics for the admin dashboard.

This is the only adapter that reads across owners, and only the
admin-guarded :class:`~app.application.admin_service.AdminService` uses it.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports import UserActivity
from app.domain.enums import TransactionType
from app.domain.money import Money
from app.infrastructure.persistence.models import AlertRow, CategoryRow, TransactionRow


class SqlAlchemyPlatformStats:
    """Implements :class:`~app.application.ports.PlatformStatsReader` with aggregate SQL."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def transaction_count(self) -> int:
        with self._sessions() as session:
            return session.scalar(select(func.count()).select_from(TransactionRow)) or 0

    def expense_volume(self) -> Money:
        with self._sessions() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(TransactionRow.amount_minor), 0)).where(
                    TransactionRow.type == TransactionType.EXPENSE.value
                )
            )
        return Money.from_minor_units(int(total or 0))

    def alerts_since(self, since: datetime) -> int:
        with self._sessions() as session:
            return (
                session.scalar(
                    select(func.count()).select_from(AlertRow).where(AlertRow.created_at >= since)
                )
                or 0
            )

    def activity_by_user(self) -> dict[str, UserActivity]:
        with self._sessions() as session:
            tx_rows = session.execute(
                select(
                    TransactionRow.owner_id,
                    func.count(),
                    func.max(TransactionRow.occurred_on),
                ).group_by(TransactionRow.owner_id)
            ).all()
            cat_rows = session.execute(
                select(CategoryRow.owner_id, func.count()).group_by(CategoryRow.owner_id)
            ).all()
        categories: dict[str, int] = {owner: int(count) for owner, count in cat_rows}
        activity = {
            owner: UserActivity(int(count), categories.get(owner, 0), last)
            for owner, count, last in tx_rows
        }
        for owner, count in categories.items():
            activity.setdefault(owner, UserActivity(0, count, None))
        return activity

    def transactions_by_day(self, since: date) -> dict[date, int]:
        with self._sessions() as session:
            rows = session.execute(
                select(TransactionRow.occurred_on, func.count())
                .where(TransactionRow.occurred_on >= since)
                .group_by(TransactionRow.occurred_on)
            ).all()
        return {day: int(count) for day, count in rows}
