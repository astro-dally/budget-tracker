"""SQLAlchemy adapters and migrations against a real SQLite file."""

from datetime import date
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.application.queries import TransactionQuery
from app.domain.category import Category
from app.domain.enums import CategorySource, TransactionType
from app.domain.errors import ConflictError, DuplicateRecurrenceError
from app.domain.money import Money, Period
from app.domain.transaction import Transaction
from app.infrastructure.persistence.database import create_db_engine, create_session_factory
from app.infrastructure.persistence.migrations import upgrade_database
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.repositories import (
    SqlAlchemyCategoryRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyUserRepository,
)


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    upgrade_database(url)
    return url


def make_owner(sessions: object, email: str = "owner@test.dev") -> str:
    from datetime import UTC, datetime

    from app.domain.user import User

    user = User.create(
        email=email, name="Owner", password_hash="x", created_at=datetime(2026, 1, 1, tzinfo=UTC)
    )
    SqlAlchemyUserRepository(sessions).add(user)  # type: ignore[arg-type]
    return user.id


def test_migrations_match_models(db_url: str) -> None:
    engine = create_db_engine(db_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"render_as_batch": True})
        assert compare_metadata(context, Base.metadata) == []
    engine.dispose()


def test_transaction_repository_round_trip_and_aggregates(db_url: str) -> None:
    engine = create_db_engine(db_url)
    sessions = create_session_factory(engine)
    owner = make_owner(sessions)
    categories = SqlAlchemyCategoryRepository(sessions, owner)
    repo = SqlAlchemyTransactionRepository(sessions, owner)
    food = Category.create("Food", "#000000", "tag")
    categories.add(food)
    with pytest.raises(ConflictError):
        categories.add(Category.create("FOOD", "#000000", "tag"))

    def tx(amount: str, day: int, source: CategorySource = CategorySource.MANUAL) -> Transaction:
        return Transaction.create(
            type=TransactionType.EXPENSE,
            amount=Money.of(amount),
            description="Sharma Dairy",
            occurred_on=date(2026, 11, day),
            category_id=food.id,
            category_source=source,
        )

    repo.add(tx("0.10", 1))
    repo.add(tx("0.20", 2, CategorySource.AUTO))
    assert repo.expense_total(food.id, Period(2026, 11)) == Money.of("0.30")
    assert repo.latest_manual_category_for("sharma dairy") == food.id
    page = repo.search(TransactionQuery(search="DAIRY", page_size=1))
    assert (page.total, len(page.items)) == (2, 1)
    assert repo.reassign_category(food.id, food.id) == 2
    stranger = make_owner(sessions, "stranger@test.dev")
    other = SqlAlchemyTransactionRepository(sessions, stranger)
    assert other.count() == 0
    assert other.get(page.items[0].id) is None
    assert SqlAlchemyCategoryRepository(sessions, stranger).find_by_name("Food") is None
    SqlAlchemyCategoryRepository(sessions, stranger).add(Category.create("Food", "#000000", "tag"))
    engine.dispose()


def test_unique_constraint_guards_recurring_occurrences(db_url: str) -> None:
    from app.domain.enums import Frequency
    from app.domain.recurrence import RecurrenceSchedule, RecurringPayment
    from app.infrastructure.persistence.repositories import (
        SqlAlchemyRecurringPaymentRepository,
    )

    engine = create_db_engine(db_url)
    sessions = create_session_factory(engine)
    owner = make_owner(sessions)
    recurring = SqlAlchemyRecurringPaymentRepository(sessions, owner)
    repo = SqlAlchemyTransactionRepository(sessions, owner)
    payment = RecurringPayment.create(
        description="Rent",
        amount=Money.of(100),
        type=TransactionType.EXPENSE,
        schedule=RecurrenceSchedule(Frequency.MONTHLY, date(2026, 11, 1)),
        category_id=None,
    )
    recurring.add(payment)

    def occurrence() -> Transaction:
        return Transaction.create(
            type=TransactionType.EXPENSE,
            amount=Money.of(100),
            description="Rent",
            occurred_on=date(2026, 11, 1),
            category_id=None,
            category_source=CategorySource.AUTO,
            recurring_id=payment.id,
        )

    repo.add(occurrence())
    with pytest.raises(DuplicateRecurrenceError):
        repo.add(occurrence())
    engine.dispose()
