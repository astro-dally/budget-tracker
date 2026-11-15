"""Read model: everything the dashboard shows, in one call."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.application.budget_service import BudgetService, BudgetStatus
from app.application.ports import CategoryRepository, Clock, TransactionRepository
from app.application.recurring_service import RecurringService, UpcomingPayment
from app.domain import analytics
from app.domain.category import Category
from app.domain.money import Money, Period
from app.domain.transaction import Transaction

TREND_MONTHS = 6


@dataclass(frozen=True, slots=True)
class CategorySpend:
    """Expenses of one category in the month."""

    category: Category
    amount: Money


@dataclass(frozen=True, slots=True)
class TrendPoint:
    """Income and expenses for one month."""

    period: Period
    income: Money
    expenses: Money


@dataclass(frozen=True, slots=True)
class DashboardOverview:
    """Aggregated figures for the dashboard page."""

    period: Period
    income: Money
    expenses: Money
    balance: Money
    budget_total: Money
    budget_spent: Money
    budget_used_percent: Decimal
    days_elapsed: int
    days_in_month: int
    spending_by_category: list[CategorySpend]
    trend: list[TrendPoint]
    budgets: list[BudgetStatus]
    recent: list[Transaction]
    upcoming: list[UpcomingPayment]


class DashboardService:
    """Composes other services into a single dashboard read model."""

    def __init__(
        self,
        transactions: TransactionRepository,
        categories: CategoryRepository,
        budgets: BudgetService,
        recurring: RecurringService,
        clock: Clock,
    ) -> None:
        self._transactions = transactions
        self._categories = categories
        self._budgets = budgets
        self._recurring = recurring
        self._clock = clock

    def overview(self, period: Period) -> DashboardOverview:
        """Build the dashboard for ``period``."""
        month_tx = self._transactions.list_between(period.start, period.end)
        month = analytics.totals(month_tx)
        categories = {c.id: c for c in self._categories.list_all()}
        by_category = [
            CategorySpend(categories[cid], amount)
            for cid, amount in analytics.expenses_by_category(month_tx).items()
            if cid is not None and cid in categories
        ]
        by_category.sort(key=lambda item: item.amount, reverse=True)

        periods = analytics.trailing_periods(period, TREND_MONTHS)
        trend_tx = self._transactions.list_between(periods[0].start, period.end)
        trend = [
            TrendPoint(p, t.income, t.expenses)
            for p, t in analytics.totals_by_period(trend_tx, periods).items()
        ]

        statuses = self._budgets.statuses(period)
        budget_total = sum((s.usage.limit for s in statuses), Money.zero())
        budget_spent = sum((s.usage.spent for s in statuses), Money.zero())
        used = budget_spent.percent_of(budget_total) if budget_total.is_positive() else Decimal(0)

        return DashboardOverview(
            period=period,
            income=month.income,
            expenses=month.expenses,
            balance=month.net,
            budget_total=budget_total,
            budget_spent=budget_spent,
            budget_used_percent=used,
            days_elapsed=self._days_elapsed(period),
            days_in_month=period.days,
            spending_by_category=by_category,
            trend=trend,
            budgets=statuses,
            recent=self._transactions.recent(6),
            upcoming=self._recurring.upcoming(5),
        )

    def _days_elapsed(self, period: Period) -> int:
        today = self._clock.today()
        if period.contains(today):
            return today.day
        return period.days if period.end < today else 0
