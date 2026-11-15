"""SQLAlchemy adapter for :class:`~app.application.ports.UserRepository`."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.enums import UserRole
from app.domain.errors import ConflictError, NotFoundError
from app.domain.user import User, normalize_email
from app.infrastructure.persistence.models import UserRow


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_domain(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        name=row.name,
        password_hash=row.password_hash,
        created_at=_aware(row.created_at) or datetime.now(UTC),
        role=UserRole(row.role),
        is_active=row.is_active,
        last_login_at=_aware(row.last_login_at),
    )


def _copy(user: User, row: UserRow) -> None:
    row.email = user.email
    row.name = user.name
    row.password_hash = user.password_hash
    row.role = user.role.value
    row.is_active = user.is_active
    row.created_at = user.created_at
    row.last_login_at = user.last_login_at


class SqlAlchemyUserRepository:
    """Stores accounts; e-mails are unique (stored normalised)."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def add(self, user: User) -> None:
        row = UserRow(id=user.id)
        _copy(user, row)
        try:
            with self._sessions.begin() as session:
                session.add(row)
        except IntegrityError as exc:
            raise ConflictError("An account with this e-mail already exists") from exc

    def update(self, user: User) -> None:
        with self._sessions.begin() as session:
            row = session.get(UserRow, user.id)
            if row is None:
                raise NotFoundError("User", user.id)
            _copy(user, row)

    def get(self, user_id: str) -> User | None:
        with self._sessions() as session:
            row = session.get(UserRow, user_id)
            return _to_domain(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        with self._sessions() as session:
            row = session.scalar(select(UserRow).where(UserRow.email == normalize_email(email)))
            return _to_domain(row) if row else None

    def list_all(self) -> list[User]:
        with self._sessions() as session:
            return [_to_domain(row) for row in session.scalars(select(UserRow))]

    def count(self) -> int:
        with self._sessions() as session:
            return session.scalar(select(func.count()).select_from(UserRow)) or 0
