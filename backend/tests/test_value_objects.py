"""Money, Period and entity invariants."""

from datetime import date
from decimal import Decimal

import pytest

from app.domain.budget import Budget
from app.domain.category import Category
from app.domain.enums import BudgetHealth, CategorySource, TransactionType
from app.domain.errors import DomainValidationError
from app.domain.money import Money, Period
from app.domain.transaction import Transaction


class TestMoney:
    def test_rounds_half_up_to_cents(self) -> None:
        assert Money.of("10.005").amount == Decimal("10.01")

    def test_rejects_float(self) -> None:
        with pytest.raises(DomainValidationError):
            Money.of(0.1)  # type: ignore[arg-type]

    def test_rejects_garbage(self) -> None:
        with pytest.raises(DomainValidationError):
            Money.of("ten")

    def test_arithmetic_is_exact(self) -> None:
        assert Money.of("0.10") + Money.of("0.20") == Money.of("0.30")
        assert Money.of("5") - Money.of("7.50") == Money.of("-2.50")

    def test_percent_of(self) -> None:
        assert Money.of("80").percent_of(Money.of("100")) == Decimal("80.0")
        with pytest.raises(DomainValidationError):
            Money.of("1").percent_of(Money.zero())

    def test_minor_units_round_trip(self) -> None:
        assert Money.from_minor_units(Money.of("1234.56").to_minor_units()) == Money.of("1234.56")


class TestPeriod:
    def test_parse_and_format(self) -> None:
        assert str(Period.parse("2026-03")) == "2026-03"

    @pytest.mark.parametrize("text", ["2026-13", "26-1", "abc", "2026"])
    def test_rejects_bad_months(self, text: str) -> None:
        with pytest.raises(DomainValidationError):
            Period.parse(text)

    def test_boundaries_and_leap_years(self) -> None:
        assert Period(2028, 2).end == date(2028, 2, 29)
        assert Period(2026, 12).next() == Period(2027, 1)
        assert Period(2026, 1).previous() == Period(2025, 12)
        assert Period(2026, 11).contains(date(2026, 11, 30))


class TestEntities:
    def test_transaction_requires_positive_amount(self) -> None:
        with pytest.raises(DomainValidationError):
            Transaction.create(
                type=TransactionType.EXPENSE,
                amount=Money.zero(),
                description="x",
                occurred_on=date(2026, 1, 1),
                category_id=None,
                category_source=CategorySource.AUTO,
            )

    def test_transaction_cleans_description(self) -> None:
        tx = Transaction.create(
            type=TransactionType.INCOME,
            amount=Money.of(1),
            description="  Salary   November ",
            occurred_on=date(2026, 1, 1),
            category_id=None,
            category_source=CategorySource.MANUAL,
        )
        assert tx.description == "Salary November"

    def test_category_validates_color(self) -> None:
        with pytest.raises(DomainValidationError):
            Category.create("Food", "red", "tag")

    @pytest.mark.parametrize("limit", ["0", "-100"])
    def test_budget_rejects_zero_or_negative_limits(self, limit: str) -> None:
        with pytest.raises(DomainValidationError):
            Budget("c1", Money.of(limit))

    @pytest.mark.parametrize(
        ("spent", "health"),
        [("79.99", BudgetHealth.OK), ("80", BudgetHealth.WARNING), ("100", BudgetHealth.EXCEEDED)],
    )
    def test_budget_health(self, spent: str, health: BudgetHealth) -> None:
        usage = Budget("c1", Money.of(100)).usage(
            category_name="Food", period=Period(2026, 1), spent=Money.of(spent)
        )
        assert usage.health is health
