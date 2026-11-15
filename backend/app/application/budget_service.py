"""Use cases: set and inspect monthly budgets."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.budget_monitor import BudgetMonitor
from app.application.ports import BudgetRepository, CategoryRepository, Clock, TransactionRepository
from app.domain.budget import Budget, BudgetUsage
from app.domain.category import Category
from app.domain.errors import NotFoundError
from app.domain.money import Money, Period


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    """A category together with its budget usage for a month."""

    category: Category
    usage: BudgetUsage


class BudgetService:
    """Manages budget limits and reports how much of each budget is used."""

    def __init__(
        self,
        budgets: BudgetRepository,
        categories: CategoryRepository,
        transactions: TransactionRepository,
        monitor: BudgetMonitor,
        clock: Clock,
    ) -> None:
        self._budgets = budgets
        self._categories = categories
        self._transactions = transactions
        self._monitor = monitor
        self._clock = clock

    def get(self, category_id: str) -> Budget | None:
        """The budget of a category, if one is set."""
        return self._budgets.get(category_id)

    def statuses(self, period: Period) -> list[BudgetStatus]:
        """Usage of every budget in ``period``, sorted by category name."""
        categories = {category.id: category for category in self._categories.list_all()}
        statuses: list[BudgetStatus] = []
        for budget in self._budgets.list_all():
            category = categories.get(budget.category_id)
            if category is None:
                continue
            spent = self._transactions.expense_total(category.id, period)
            usage = budget.usage(category_name=category.name, period=period, spent=spent)
            statuses.append(BudgetStatus(category, usage))
        return sorted(statuses, key=lambda status: status.category.name.lower())

    def set_limit(self, category_id: str, limit: Money) -> Budget:
        """Create or change a limit, then re-check this month's alerts.

        Lowering a limit below current spending raises the alert immediately.
        """
        if self._categories.get(category_id) is None:
            raise NotFoundError("Category", category_id)
        budget = Budget(category_id=category_id, monthly_limit=limit)
        self._budgets.save(budget)
        self._monitor.check(category_id, Period.of(self._clock.today()))
        return budget

    def remove_limit(self, category_id: str) -> None:
        """Remove a category's limit; it will no longer raise alerts."""
        if self._categories.get(category_id) is None:
            raise NotFoundError("Category", category_id)
        self._budgets.delete(category_id)
