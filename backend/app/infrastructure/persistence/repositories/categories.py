"""SQLAlchemy adapter for :class:`~app.application.ports.CategoryRepository` (owner-scoped)."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.category import Category
from app.domain.errors import ConflictError, NotFoundError
from app.infrastructure.persistence.models import CategoryRow


def _key(name: str) -> str:
    return " ".join(name.split()).lower()


def _to_domain(row: CategoryRow) -> Category:
    return Category(
        id=row.id, name=row.name, color=row.color, icon=row.icon, is_system=row.is_system
    )


class SqlAlchemyCategoryRepository:
    """Stores one user's categories; names are unique per user, case-insensitively."""

    def __init__(self, sessions: sessionmaker[Session], owner_id: str) -> None:
        self._sessions = sessions
        self._owner_id = owner_id

    def _mine(self, session: Session, category_id: str) -> CategoryRow | None:
        return session.scalar(
            select(CategoryRow).where(
                CategoryRow.id == category_id, CategoryRow.owner_id == self._owner_id
            )
        )

    def add(self, category: Category) -> None:
        try:
            with self._sessions.begin() as session:
                session.add(
                    CategoryRow(
                        id=category.id,
                        owner_id=self._owner_id,
                        name=category.name,
                        name_key=_key(category.name),
                        color=category.color,
                        icon=category.icon,
                        is_system=category.is_system,
                    )
                )
        except IntegrityError as exc:
            raise ConflictError(f"A category named '{category.name}' already exists") from exc

    def update(self, category: Category) -> None:
        with self._sessions.begin() as session:
            row = self._mine(session, category.id)
            if row is None:
                raise NotFoundError("Category", category.id)
            row.name = category.name
            row.name_key = _key(category.name)
            row.color = category.color
            row.icon = category.icon
            row.is_system = category.is_system

    def delete(self, category_id: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(CategoryRow).where(
                    CategoryRow.id == category_id, CategoryRow.owner_id == self._owner_id
                )
            )

    def get(self, category_id: str) -> Category | None:
        with self._sessions() as session:
            row = self._mine(session, category_id)
            return _to_domain(row) if row else None

    def list_all(self) -> list[Category]:
        with self._sessions() as session:
            rows = session.scalars(
                select(CategoryRow).where(CategoryRow.owner_id == self._owner_id)
            )
            return [_to_domain(row) for row in rows]

    def find_by_name(self, name: str) -> Category | None:
        with self._sessions() as session:
            row = session.scalar(
                select(CategoryRow).where(
                    CategoryRow.owner_id == self._owner_id, CategoryRow.name_key == _key(name)
                )
            )
            return _to_domain(row) if row else None
