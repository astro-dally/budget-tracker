"""SQLAlchemy ORM models (persistence representation, separate from domain entities).

Multi-tenancy lives here, not in the domain: every user-data table has an
``owner_id`` and the repository adapters are constructed for one owner, so a
service can never read or change another user's rows.

Money is stored as integer minor units (cents/paise) so sums are exact on
every database, including SQLite, which has no native decimal type.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    MetaData,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utc_now() -> datetime:
    """Default timestamp for inserted rows."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base; the naming convention keeps future migrations deterministic."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def owner_column() -> Mapped[str]:
    """The owning user. Every user-data table has one; adapters filter on it."""
    return mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)


class UserRow(Base):
    """Table ``users``."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CategoryRow(Base):
    """Table ``categories``."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("owner_id", "name_key"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_id: Mapped[str] = owner_column()
    name: Mapped[str] = mapped_column(String(50))
    name_key: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(7))
    icon: Mapped[str] = mapped_column(String(40))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class BudgetRow(Base):
    """Table ``budgets`` (one row per category)."""

    __tablename__ = "budgets"

    owner_id: Mapped[str] = owner_column()
    category_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )
    limit_minor: Mapped[int] = mapped_column(BigInteger)


class CategoryRuleRow(Base):
    """Table ``category_rules``."""

    __tablename__ = "category_rules"
    __table_args__ = (UniqueConstraint("owner_id", "keyword"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_id: Mapped[str] = owner_column()
    keyword: Mapped[str] = mapped_column(String(50))
    category_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )


class RecurringPaymentRow(Base):
    """Table ``recurring_payments``."""

    __tablename__ = "recurring_payments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_id: Mapped[str] = owner_column()
    description: Mapped[str] = mapped_column(String(200))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(10))
    category_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    frequency: Mapped[str] = mapped_column(String(10))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_generated_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class TransactionRow(Base):
    """Table ``transactions``.

    The unique ``(recurring_id, occurred_on)`` constraint is the database-level
    idempotency guard for recurring generation.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("recurring_id", "occurred_on", name="uq_transactions_recurrence"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_id: Mapped[str] = owner_column()
    type: Mapped[str] = mapped_column(String(10), index=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(String(200))
    description_key: Mapped[str] = mapped_column(String(200), index=True)
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    category_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("categories.id"), nullable=True, index=True
    )
    category_source: Mapped[str] = mapped_column(String(10))
    recurring_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("recurring_payments.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AlertRow(Base):
    """Table ``alerts``.

    The unique ``(category_id, period, rule_key)`` constraint makes each
    threshold fire at most once per category per month.
    """

    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("category_id", "period", "rule_key", name="uq_alerts_once_per_period"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_id: Mapped[str] = owner_column()
    category_id: Mapped[str] = mapped_column(String(32))
    category_name: Mapped[str] = mapped_column(String(50))
    period: Mapped[str] = mapped_column(String(7))
    rule_key: Mapped[str] = mapped_column(String(40))
    level: Mapped[str] = mapped_column(String(10))
    threshold: Mapped[str] = mapped_column(String(12))
    message: Mapped[str] = mapped_column(String(300))
    spent_minor: Mapped[int] = mapped_column(BigInteger)
    limit_minor: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
