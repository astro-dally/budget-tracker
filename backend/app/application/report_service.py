"""Use cases: list available reports and generate one."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from app.application.ports import BudgetRepository, CategoryRepository, TransactionRepository
from app.domain.budget import Budget
from app.domain.category import Category
from app.domain.money import Period
from app.domain.reports import Report, ReportDataSource, ReportRegistry, ReportStrategy
from app.domain.transaction import Transaction


class RepositoryReportDataSource:
    """Adapter exposing repositories through the read-only :class:`ReportDataSource` port."""

    def __init__(
        self,
        transactions: TransactionRepository,
        categories: CategoryRepository,
        budgets: BudgetRepository,
    ) -> None:
        self._transactions = transactions
        self._categories = categories
        self._budgets = budgets

    def transactions_between(self, start: date, end: date) -> Sequence[Transaction]:
        return self._transactions.list_between(start, end)

    def categories(self) -> Sequence[Category]:
        return self._categories.list_all()

    def budgets(self) -> Sequence[Budget]:
        return self._budgets.list_all()


class ReportService:
    """Selects a :class:`ReportStrategy` from the registry and runs it."""

    def __init__(self, registry: ReportRegistry, data: ReportDataSource) -> None:
        self._registry = registry
        self._data = data

    def available(self) -> list[ReportStrategy]:
        """Every registered report type."""
        return self._registry.available()

    def generate(self, key: str, period: Period) -> Report:
        """Run the report ``key`` for ``period``."""
        return self._registry.get(key).generate(period, self._data)
