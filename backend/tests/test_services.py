"""Application services against in-memory repositories."""

from datetime import date

import pytest

from app.application.category_service import CategoryInput
from app.application.queries import SortDirection, SortField, TransactionQuery
from app.application.transaction_service import TransactionInput
from app.domain.enums import CategorySource, TransactionType
from app.domain.errors import (
    ConflictError,
    DomainValidationError,
    NotFoundError,
)
from app.domain.money import Money, Period
from tests.conftest import World


def test_expenses_without_category_are_auto_categorised(world: World) -> None:
    transport = world.category("Transport")
    world.rules.create("uber", transport.id)
    tx = world.spend("250", None, text="Uber to office")
    assert (tx.category_id, tx.category_source) == (transport.id, CategorySource.AUTO)


def test_explicit_category_is_manual(world: World) -> None:
    food = world.category("Food")
    assert world.spend("10", food).category_source is CategorySource.MANUAL


def test_income_is_left_uncategorised(world: World) -> None:
    tx = world.transactions.record(
        TransactionInput(TransactionType.INCOME, Money.of(100), "Refund", date(2026, 11, 1))
    )
    assert tx.category_id is None


def test_unknown_category_is_rejected(world: World) -> None:
    with pytest.raises(NotFoundError):
        world.transactions.record(
            TransactionInput(TransactionType.EXPENSE, Money.of(1), "x", date(2026, 11, 1), "nope")
        )


def test_update_and_delete(world: World) -> None:
    food = world.category("Food")
    tx = world.spend("10", food)
    updated = world.transactions.update(
        tx.id, TransactionInput(TransactionType.EXPENSE, Money.of(25), "Lunch", tx.occurred_on)
    )
    assert updated.category_source is CategorySource.AUTO
    assert world.transactions.get(tx.id).amount == Money.of(25)
    world.transactions.delete(tx.id)
    with pytest.raises(NotFoundError):
        world.transactions.delete(tx.id)


def test_search_filters_sorts_and_pages(world: World) -> None:
    food = world.category("Food")
    for amount in ("30", "10", "20"):
        world.spend(amount, food, text=f"Coffee {amount}")
    world.spend("99", food, text="Book")
    page = world.transactions.search(
        TransactionQuery(
            search="coffee",
            sort_by=SortField.AMOUNT,
            sort_direction=SortDirection.ASC,
            page_size=2,
        )
    )
    assert page.total == 3
    assert page.pages == 2
    assert [t.amount for t in page.items] == [Money.of(10), Money.of(20)]


def test_query_validation() -> None:
    with pytest.raises(DomainValidationError):
        TransactionQuery(page=0)
    with pytest.raises(DomainValidationError):
        TransactionQuery(date_from=date(2026, 2, 1), date_to=date(2026, 1, 1))


def test_category_names_are_unique_case_insensitively(world: World) -> None:
    world.category("Food")
    with pytest.raises(ConflictError):
        world.category("  food ")


def test_category_update_changes_budget(world: World) -> None:
    food = world.category("Food", 100)
    world.categories.update(food.id, CategoryInput("Food & Dining", "#000000", "utensils", None))
    details = world.categories.get(food.id)
    assert details.category.name == "Food & Dining"
    assert details.budget is None


def test_deleting_a_category_moves_its_data_to_uncategorized(world: World) -> None:
    food = world.category("Food", 500)
    world.rules.create("pizza", food.id)
    tx = world.spend("10", food)
    world.categories.delete(food.id)
    fallback = world.categories_repo.find_by_name("Uncategorized")
    assert fallback is not None
    assert world.transactions.get(tx.id).category_id == fallback.id
    assert world.rules.list_all() == []
    assert world.budgets.get(food.id) is None


def test_system_category_is_protected(world: World) -> None:
    fallback = world.categories.ensure_system_categories()
    with pytest.raises(ConflictError):
        world.categories.delete(fallback.id)
    with pytest.raises(ConflictError):
        world.categories.update(fallback.id, CategoryInput("Other", "#000000", "tag"))


def test_rules_are_unique_and_validated(world: World) -> None:
    food = world.category("Food")
    rule = world.rules.create("Pizza", food.id)
    assert rule.keyword == "pizza"
    with pytest.raises(ConflictError):
        world.rules.create("PIZZA", food.id)
    with pytest.raises(NotFoundError):
        world.rules.create("burger", "missing")
    world.rules.update(rule.id, "pizza hut", food.id)
    world.rules.delete(rule.id)
    with pytest.raises(NotFoundError):
        world.rules.delete(rule.id)


def test_suggestion_explains_itself(world: World) -> None:
    food = world.category("Food & Dining")
    suggestion = world.categorization.suggest("Swiggy order 123")
    assert suggestion.category.id == food.id
    assert suggestion.reason == "merchant Swiggy"
    with pytest.raises(DomainValidationError):
        world.categorization.suggest("   ")


def test_budget_statuses(world: World) -> None:
    food = world.category("Food", 1000)
    world.category("Misc")
    world.spend("850", food)
    [status] = world.budgets.statuses(Period(2026, 11))
    assert status.usage.health.value == "warning"
    assert status.usage.remaining == Money.of(150)
    with pytest.raises(NotFoundError):
        world.budgets.set_limit("missing", Money.of(1))


def test_alert_service(world: World) -> None:
    world.spend("100", world.category("Food", 100))
    assert world.alerts.unread_count() == 2
    first = world.alerts.list_all()[0]
    world.alerts.mark_read(first.id)
    assert world.alerts.unread_count() == 1
    assert world.alerts.mark_all_read() == 1
    with pytest.raises(NotFoundError):
        world.alerts.mark_read("missing")


def test_dashboard_overview(world: World) -> None:
    food = world.category("Food", 1000)
    world.transactions.record(
        TransactionInput(TransactionType.INCOME, Money.of(3000), "Salary", date(2026, 11, 1))
    )
    world.spend("400", food)
    overview = world.dashboard.overview(Period(2026, 11))
    assert overview.balance == Money.of(2600)
    assert overview.budget_used_percent == 40
    assert overview.days_elapsed == 14
    assert len(overview.trend) == 6
    assert overview.spending_by_category[0].category.id == food.id
    assert world.dashboard.overview(Period(2026, 10)).days_elapsed == 31
    assert world.dashboard.overview(Period(2027, 1)).days_elapsed == 0
