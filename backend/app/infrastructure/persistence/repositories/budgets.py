"""SQLAlchemy adapter for :class:`~app.application.ports.BudgetRepository` (owner-scoped)."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.budget import Budget
from app.domain.money import Money
from app.infrastructure.persistence.models import BudgetRow


def _to_domain(row: BudgetRow) -> Budget:
    return Budget(
        category_id=row.category_id, monthly_limit=Money.from_minor_units(row.limit_minor)
    )


class SqlAlchemyBudgetRepository:
    """Stores one budget per category for one user."""

    def __init__(self, sessions: sessionmaker[Session], owner_id: str) -> None:
        self._sessions = sessions
        self._owner_id = owner_id

    def _mine(self, session: Session, category_id: str) -> BudgetRow | None:
        return session.scalar(
            select(BudgetRow).where(
                BudgetRow.category_id == category_id, BudgetRow.owner_id == self._owner_id
            )
        )

    def get(self, category_id: str) -> Budget | None:
        with self._sessions() as session:
            row = self._mine(session, category_id)
            return _to_domain(row) if row else None

    def save(self, budget: Budget) -> None:
        with self._sessions.begin() as session:
            row = self._mine(session, budget.category_id)
            minor = budget.monthly_limit.to_minor_units()
            if row is None:
                session.add(
                    BudgetRow(
                        owner_id=self._owner_id, category_id=budget.category_id, limit_minor=minor
                    )
                )
            else:
                row.limit_minor = minor

    def delete(self, category_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(BudgetRow).where(
                    BudgetRow.category_id == category_id, BudgetRow.owner_id == self._owner_id
                )
            )

    def list_all(self) -> list[Budget]:
        with self._sessions() as session:
            rows = session.scalars(select(BudgetRow).where(BudgetRow.owner_id == self._owner_id))
            return [_to_domain(row) for row in rows]
