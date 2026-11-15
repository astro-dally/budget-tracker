"""SQLAlchemy adapter for :class:`~app.application.ports.CategoryRuleRepository` (owner-scoped)."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.category_rule import CategoryRule
from app.domain.errors import ConflictError, NotFoundError
from app.infrastructure.persistence.models import CategoryRuleRow


def _to_domain(row: CategoryRuleRow) -> CategoryRule:
    return CategoryRule(id=row.id, keyword=row.keyword, category_id=row.category_id)


class SqlAlchemyCategoryRuleRepository:
    """Stores one user's keyword rules (keywords unique per user)."""

    def __init__(self, sessions: sessionmaker[Session], owner_id: str) -> None:
        self._sessions = sessions
        self._owner_id = owner_id

    def _mine(self, session: Session, rule_id: str) -> CategoryRuleRow | None:
        return session.scalar(
            select(CategoryRuleRow).where(
                CategoryRuleRow.id == rule_id, CategoryRuleRow.owner_id == self._owner_id
            )
        )

    def add(self, rule: CategoryRule) -> None:
        try:
            with self._sessions.begin() as session:
                session.add(
                    CategoryRuleRow(
                        id=rule.id,
                        owner_id=self._owner_id,
                        keyword=rule.keyword,
                        category_id=rule.category_id,
                    )
                )
        except IntegrityError as exc:
            raise ConflictError(f"A rule for '{rule.keyword}' already exists") from exc

    def update(self, rule: CategoryRule) -> None:
        with self._sessions.begin() as session:
            row = self._mine(session, rule.id)
            if row is None:
                raise NotFoundError("Rule", rule.id)
            row.keyword = rule.keyword
            row.category_id = rule.category_id

    def delete(self, rule_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(CategoryRuleRow).where(
                    CategoryRuleRow.id == rule_id, CategoryRuleRow.owner_id == self._owner_id
                )
            )

    def get(self, rule_id: str) -> CategoryRule | None:
        with self._sessions() as session:
            row = self._mine(session, rule_id)
            return _to_domain(row) if row else None

    def list_rules(self) -> list[CategoryRule]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CategoryRuleRow).where(CategoryRuleRow.owner_id == self._owner_id)
            )
            return [_to_domain(row) for row in rows]

    def find_by_keyword(self, keyword: str) -> CategoryRule | None:
        normalized = " ".join(keyword.split()).lower()
        with self._sessions() as session:
            row = session.scalar(
                select(CategoryRuleRow).where(
                    CategoryRuleRow.owner_id == self._owner_id,
                    CategoryRuleRow.keyword == normalized,
                )
            )
            return _to_domain(row) if row else None

    def delete_for_category(self, category_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(CategoryRuleRow).where(
                    CategoryRuleRow.owner_id == self._owner_id,
                    CategoryRuleRow.category_id == category_id,
                )
            )
