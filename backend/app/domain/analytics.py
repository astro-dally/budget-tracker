"""Pure aggregation helpers shared by reports and the dashboard (DRY)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.money import Money, Period
from app.domain.transaction import Transaction


@dataclass(frozen=True, slots=True)
class Totals:
    """Income and expense totals for a set of transactions."""

    income: Money
    expenses: Money

    @property
    def net(self) -> Money:
        """Income minus expenses."""
        return self.income - self.expenses


def totals(transactions: Iterable[Transaction]) -> Totals:
    """Sum income and expenses."""
    income = Money.zero()
    expenses = Money.zero()
    for tx in transactions:
        if tx.is_expense:
            expenses = expenses + tx.amount
        else:
            income = income + tx.amount
    return Totals(income=income, expenses=expenses)


def expenses_by_category(transactions: Iterable[Transaction]) -> dict[str | None, Money]:
    """Sum expenses per category id."""
    sums: dict[str | None, Money] = defaultdict(Money.zero)
    for tx in transactions:
        if tx.is_expense:
            sums[tx.category_id] = sums[tx.category_id] + tx.amount
    return dict(sums)


def expense_counts_by_category(transactions: Iterable[Transaction]) -> dict[str | None, int]:
    """Count expenses per category id."""
    counts: dict[str | None, int] = defaultdict(int)
    for tx in transactions:
        if tx.is_expense:
            counts[tx.category_id] += 1
    return dict(counts)


def trailing_periods(end: Period, count: int) -> list[Period]:
    """The ``count`` months ending with ``end``, oldest first."""
    periods = [end]
    while len(periods) < count:
        periods.append(periods[-1].previous())
    return list(reversed(periods))


def totals_by_period(
    transactions: Iterable[Transaction], periods: Iterable[Period]
) -> dict[Period, Totals]:
    """Income/expense totals for each requested period."""
    grouped: dict[Period, list[Transaction]] = {period: [] for period in periods}
    for tx in transactions:
        if tx.period in grouped:
            grouped[tx.period].append(tx)
    return {period: totals(items) for period, items in grouped.items()}
