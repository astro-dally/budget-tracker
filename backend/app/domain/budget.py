"""The :class:`Budget` entity and the :class:`BudgetUsage` snapshot it produces."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import BudgetHealth
from app.domain.errors import DomainValidationError
from app.domain.money import Money, Period

WARNING_PERCENT = Decimal(80)
EXCEEDED_PERCENT = Decimal(100)


@dataclass(frozen=True, slots=True)
class Budget:
    """A monthly spending limit for one category.

    Invariant: the limit is strictly positive. A zero or negative limit is
    meaningless (every expense would be "over budget" and percentages would
    divide by zero), so "no budget" is modelled by the absence of a Budget.
    """

    category_id: str
    monthly_limit: Money

    def __post_init__(self) -> None:
        if not self.monthly_limit.is_positive():
            raise DomainValidationError("A budget limit must be greater than zero")

    def usage(self, *, category_name: str, period: Period, spent: Money) -> BudgetUsage:
        """Return how much of this budget has been used in ``period``."""
        return BudgetUsage(
            category_id=self.category_id,
            category_name=category_name,
            period=period,
            limit=self.monthly_limit,
            spent=spent,
        )


@dataclass(frozen=True, slots=True)
class BudgetUsage:
    """Immutable snapshot of a budget's consumption, evaluated by alert rules."""

    category_id: str
    category_name: str
    period: Period
    limit: Money
    spent: Money

    @property
    def remaining(self) -> Money:
        """Money left before the limit (negative when over budget)."""
        return self.limit - self.spent

    @property
    def percent_used(self) -> Decimal:
        """Spent as a percentage of the limit, one decimal place."""
        return self.spent.percent_of(self.limit)

    def has_reached(self, percent: Decimal) -> bool:
        """Exact check (no rounding) of whether spending reached ``percent`` of the limit."""
        return self.spent.amount * 100 >= self.limit.amount * percent

    @property
    def health(self) -> BudgetHealth:
        """Traffic-light status: green below 80%, amber from 80%, red from 100%."""
        if self.has_reached(EXCEEDED_PERCENT):
            return BudgetHealth.EXCEEDED
        if self.has_reached(WARNING_PERCENT):
            return BudgetHealth.WARNING
        return BudgetHealth.OK
