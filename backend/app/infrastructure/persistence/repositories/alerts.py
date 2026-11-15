"""SQLAlchemy adapter for :class:`~app.application.ports.AlertRepository` (owner-scoped)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.alert import Alert
from app.domain.enums import AlertLevel
from app.domain.money import Money, Period
from app.infrastructure.persistence.models import AlertRow


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_domain(row: AlertRow) -> Alert:
    return Alert(
        id=row.id,
        category_id=row.category_id,
        category_name=row.category_name,
        period=Period.parse(row.period),
        rule_key=row.rule_key,
        level=AlertLevel(row.level),
        threshold=Decimal(row.threshold),
        message=row.message,
        spent=Money.from_minor_units(row.spent_minor),
        limit=Money.from_minor_units(row.limit_minor),
        created_at=_aware(row.created_at),
        is_read=row.is_read,
    )


class SqlAlchemyAlertRepository:
    """Stores alert history; the unique constraint de-duplicates alerts atomically."""

    def __init__(self, sessions: sessionmaker[Session], owner_id: str) -> None:
        self._sessions = sessions
        self._owner_id = owner_id
        self._is_mine = AlertRow.owner_id == owner_id

    def add_if_absent(self, alert: Alert) -> bool:
        row = AlertRow(
            id=alert.id,
            owner_id=self._owner_id,
            category_id=alert.category_id,
            category_name=alert.category_name,
            period=str(alert.period),
            rule_key=alert.rule_key,
            level=alert.level.value,
            threshold=str(alert.threshold),
            message=alert.message,
            spent_minor=alert.spent.to_minor_units(),
            limit_minor=alert.limit.to_minor_units(),
            created_at=alert.created_at,
            is_read=alert.is_read,
        )
        try:
            with self._sessions.begin() as session:
                session.add(row)
        except IntegrityError:
            return False
        return True

    def list_recent(self, limit: int, unread_only: bool) -> list[Alert]:
        statement = (
            select(AlertRow).where(self._is_mine).order_by(AlertRow.created_at.desc()).limit(limit)
        )
        if unread_only:
            statement = statement.where(self._is_mine, AlertRow.is_read.is_(False))
        with self._sessions() as session:
            return [_to_domain(row) for row in session.scalars(statement)]

    def mark_read(self, alert_id: str) -> bool:
        with self._sessions.begin() as session:
            row = session.scalar(select(AlertRow).where(AlertRow.id == alert_id, self._is_mine))
            if row is None:
                return False
            row.is_read = True
            return True

    def mark_all_read(self) -> int:
        with self._sessions.begin() as session:
            count = session.scalar(
                select(func.count())
                .select_from(AlertRow)
                .where(self._is_mine, AlertRow.is_read.is_(False))
            )
            session.execute(
                update(AlertRow)
                .where(self._is_mine, AlertRow.is_read.is_(False))
                .values(is_read=True)
            )
        return count or 0

    def unread_count(self) -> int:
        with self._sessions() as session:
            return (
                session.scalar(
                    select(func.count())
                    .select_from(AlertRow)
                    .where(self._is_mine, AlertRow.is_read.is_(False))
                )
                or 0
            )
