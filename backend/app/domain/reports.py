"""Strategy pattern: reports, selected at runtime through a registry.

``ReportStrategy`` is the *Strategy* interface; ``MonthlySummaryReport``,
``CategoryWiseReport`` and ``SpendingTrendReport`` are *Concrete Strategies*.
``ReportRegistry`` maps a report key (``/reports/{type}``) to a strategy, so
the API and UI discover report types dynamically: adding a report is one
new class plus one ``register`` call in the composition root (Open/Closed).

Every strategy returns the same generic :class:`Report` shape (columns,
rows, headline metrics and a chart hint). The frontend renders any report
from that shape, so a new strategy needs no frontend changes either.
"""

from __future__ import annotations

import calendar
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar, Protocol

from app.domain import analytics
from app.domain.budget import Budget
from app.domain.category import Category
from app.domain.errors import ConflictError, NotFoundError
from app.domain.money import Money, Period
from app.domain.transaction import Transaction

type CellValue = str | int | Decimal


class ColumnKind(StrEnum):
    """How the UI should format a column or metric."""

    TEXT = "text"
    MONEY = "money"
    PERCENT = "percent"
    NUMBER = "number"


class ChartKind(StrEnum):
    """Which chart best visualises a report."""

    BAR = "bar"
    PIE = "pie"
    LINE = "line"


@dataclass(frozen=True, slots=True)
class ReportColumn:
    """A table column."""

    key: str
    label: str
    kind: ColumnKind


@dataclass(frozen=True, slots=True)
class ReportMetric:
    """A headline number shown above the table."""

    label: str
    value: CellValue
    kind: ColumnKind


@dataclass(frozen=True, slots=True)
class ChartSpec:
    """Tells the UI which chart to draw from the rows."""

    kind: ChartKind
    x_key: str
    y_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Report:
    """The generic output of every report strategy."""

    key: str
    title: str
    period: Period
    columns: tuple[ReportColumn, ...]
    rows: tuple[Mapping[str, CellValue], ...]
    metrics: tuple[ReportMetric, ...]
    chart: ChartSpec | None = None


class ReportDataSource(Protocol):
    """Read-only data a report needs (Interface Segregation: no write methods)."""

    def transactions_between(self, start: date, end: date) -> Sequence[Transaction]:
        """Transactions with ``start <= occurred_on <= end``."""
        ...

    def categories(self) -> Sequence[Category]:
        """All categories."""
        ...

    def budgets(self) -> Sequence[Budget]:
        """All budgets."""
        ...


class ReportStrategy(ABC):
    """Strategy interface for reports."""

    key: ClassVar[str]
    title: ClassVar[str]
    description: ClassVar[str]

    @abstractmethod
    def generate(self, period: Period, data: ReportDataSource) -> Report:
        """Build the report for ``period``."""


def _ratio(part: Money, whole: Money) -> Decimal:
    return part.percent_of(whole) if whole.is_positive() else Decimal("0.0")


class MonthlySummaryReport(ReportStrategy):
    """Income vs expenses for one month, broken down by week."""

    key = "monthly-summary"
    title = "Monthly summary"
    description = "Income, spending and savings for the month, week by week."

    def generate(self, period: Period, data: ReportDataSource) -> Report:
        transactions = data.transactions_between(period.start, period.end)
        rows: list[dict[str, CellValue]] = []
        for first_day in range(1, period.days + 1, 7):
            last_day = min(first_day + 6, period.days)
            week = [tx for tx in transactions if first_day <= tx.occurred_on.day <= last_day]
            week_totals = analytics.totals(week)
            rows.append(
                {
                    "week": f"{first_day}–{last_day} {calendar.month_abbr[period.month]}",
                    "income": week_totals.income.amount,
                    "expenses": week_totals.expenses.amount,
                    "net": week_totals.net.amount,
                }
            )
        month = analytics.totals(transactions)
        expenses = [tx for tx in transactions if tx.is_expense]
        largest = max(expenses, key=lambda tx: tx.amount, default=None)
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=(
                ReportColumn("week", "Week", ColumnKind.TEXT),
                ReportColumn("income", "Income", ColumnKind.MONEY),
                ReportColumn("expenses", "Expenses", ColumnKind.MONEY),
                ReportColumn("net", "Net", ColumnKind.MONEY),
            ),
            rows=tuple(rows),
            metrics=(
                ReportMetric("Income", month.income.amount, ColumnKind.MONEY),
                ReportMetric("Expenses", month.expenses.amount, ColumnKind.MONEY),
                ReportMetric("Net savings", month.net.amount, ColumnKind.MONEY),
                ReportMetric("Savings rate", _ratio(month.net, month.income), ColumnKind.PERCENT),
                ReportMetric(
                    "Largest expense",
                    largest.amount.amount if largest else Decimal("0.00"),
                    ColumnKind.MONEY,
                ),
                ReportMetric("Transactions", len(transactions), ColumnKind.NUMBER),
            ),
            chart=ChartSpec(ChartKind.BAR, "week", ("income", "expenses")),
        )


class CategoryWiseReport(ReportStrategy):
    """Spending per category against its budget."""

    key = "category-wise"
    title = "Spending by category"
    description = "Where the money went, compared with each category's budget."

    def generate(self, period: Period, data: ReportDataSource) -> Report:
        transactions = data.transactions_between(period.start, period.end)
        spent = analytics.expenses_by_category(transactions)
        counts = analytics.expense_counts_by_category(transactions)
        budgets = {budget.category_id: budget for budget in data.budgets()}
        total = analytics.totals(transactions).expenses
        rows: list[dict[str, CellValue]] = []
        over_budget = 0
        for category in data.categories():
            amount = spent.get(category.id, Money.zero())
            budget = budgets.get(category.id)
            if not amount.is_positive() and budget is None:
                continue
            used: CellValue = ""
            if budget is not None:
                usage = budget.usage(category_name=category.name, period=period, spent=amount)
                used = usage.percent_used
                over_budget += usage.has_reached(Decimal(100))
            rows.append(
                {
                    "category": category.name,
                    "color": category.color,
                    "spent": amount.amount,
                    "budget": budget.monthly_limit.amount if budget else "",
                    "used": used,
                    "share": _ratio(amount, total),
                    "transactions": counts.get(category.id, 0),
                }
            )
        rows.sort(key=lambda row: Decimal(row["spent"]), reverse=True)
        top = str(rows[0]["category"]) if rows and Decimal(rows[0]["spent"]) > 0 else "—"
        budgeted = sum((budget.monthly_limit for budget in budgets.values()), Money.zero())
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=(
                ReportColumn("category", "Category", ColumnKind.TEXT),
                ReportColumn("spent", "Spent", ColumnKind.MONEY),
                ReportColumn("budget", "Budget", ColumnKind.MONEY),
                ReportColumn("used", "Budget used", ColumnKind.PERCENT),
                ReportColumn("share", "Share of spending", ColumnKind.PERCENT),
                ReportColumn("transactions", "Transactions", ColumnKind.NUMBER),
            ),
            rows=tuple(rows),
            metrics=(
                ReportMetric("Total spent", total.amount, ColumnKind.MONEY),
                ReportMetric("Total budgeted", budgeted.amount, ColumnKind.MONEY),
                ReportMetric("Categories over budget", over_budget, ColumnKind.NUMBER),
                ReportMetric("Top category", top, ColumnKind.TEXT),
            ),
            chart=ChartSpec(ChartKind.PIE, "category", ("spent",)),
        )


class SpendingTrendReport(ReportStrategy):
    """Six-month income and spending trend ending at the selected month."""

    key = "spending-trend"
    title = "Six-month trend"
    description = "How income and spending moved over the last six months."
    months = 6

    def generate(self, period: Period, data: ReportDataSource) -> Report:
        periods = analytics.trailing_periods(period, self.months)
        transactions = data.transactions_between(periods[0].start, period.end)
        by_period = analytics.totals_by_period(transactions, periods)
        rows: list[dict[str, CellValue]] = [
            {
                "month": f"{calendar.month_abbr[p.month]} {p.year}",
                "income": totals.income.amount,
                "expenses": totals.expenses.amount,
                "net": totals.net.amount,
                "savings_rate": _ratio(totals.net, totals.income),
            }
            for p, totals in by_period.items()
        ]
        spend = [totals.expenses for totals in by_period.values()]
        income = [totals.income for totals in by_period.values()]
        current, previous = spend[-1], spend[-2]
        change = (
            ((current.amount - previous.amount) * 100 / previous.amount).quantize(Decimal("0.1"))
            if previous.is_positive()
            else Decimal("0.0")
        )
        months = Decimal(len(periods))
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=(
                ReportColumn("month", "Month", ColumnKind.TEXT),
                ReportColumn("income", "Income", ColumnKind.MONEY),
                ReportColumn("expenses", "Expenses", ColumnKind.MONEY),
                ReportColumn("net", "Net", ColumnKind.MONEY),
                ReportColumn("savings_rate", "Savings rate", ColumnKind.PERCENT),
            ),
            rows=tuple(rows),
            metrics=(
                ReportMetric(
                    "Average monthly spend",
                    Money(sum((m.amount for m in spend), Decimal(0)) / months).amount,
                    ColumnKind.MONEY,
                ),
                ReportMetric(
                    "Average monthly income",
                    Money(sum((m.amount for m in income), Decimal(0)) / months).amount,
                    ColumnKind.MONEY,
                ),
                ReportMetric("Spend change vs last month", change, ColumnKind.PERCENT),
            ),
            chart=ChartSpec(ChartKind.LINE, "month", ("income", "expenses")),
        )


class ReportRegistry:
    """Maps report keys to strategies (a simple registry/factory)."""

    def __init__(self) -> None:
        self._strategies: dict[str, ReportStrategy] = {}

    def register(self, strategy: ReportStrategy) -> ReportRegistry:
        """Add a strategy; keys must be unique."""
        if strategy.key in self._strategies:
            raise ConflictError(f"Report type '{strategy.key}' is already registered")
        self._strategies[strategy.key] = strategy
        return self

    def get(self, key: str) -> ReportStrategy:
        """Return the strategy for ``key``."""
        try:
            return self._strategies[key]
        except KeyError:
            raise NotFoundError("Report type", key) from None

    def available(self) -> list[ReportStrategy]:
        """All registered strategies in registration order."""
        return list(self._strategies.values())
