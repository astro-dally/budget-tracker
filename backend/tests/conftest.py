"""Shared fixtures: a fully wired application core running on in-memory fakes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest

from app.application.alert_service import AlertService
from app.application.budget_monitor import BudgetMonitor
from app.application.budget_service import BudgetService
from app.application.categorization_service import CategorizationService
from app.application.category_service import CategoryInput, CategoryService
from app.application.dashboard_service import DashboardService
from app.application.observers import NotificationDispatcher
from app.application.recurring_service import RecurringService
from app.application.report_service import ReportService, RepositoryReportDataSource
from app.application.rule_service import RuleService
from app.application.transaction_service import TransactionInput, TransactionService
from app.container import build_report_registry
from app.domain.alert_rules import PercentageThresholdRule
from app.domain.categorization import (
    CategorizationChainBuilder,
    DefaultCategoryHandler,
    KeywordRuleHandler,
    MerchantRuleHandler,
    UserDefinedRuleHandler,
)
from app.domain.category import Category
from app.domain.enums import TransactionType
from app.domain.money import Money
from app.domain.transaction import Transaction
from app.infrastructure.merchant_directory import DEFAULT_MERCHANTS
from tests.fakes import (
    FixedClock,
    InMemoryAlertRepository,
    InMemoryBudgetRepository,
    InMemoryCategoryRepository,
    InMemoryRecurringRepository,
    InMemoryRuleRepository,
    InMemoryTransactionRepository,
    RecordingChannel,
    RecordingObserver,
)

TODAY = date(2026, 11, 14)


@dataclass
class World:
    """Every service wired against fakes, plus handles for assertions."""

    clock: FixedClock
    transactions_repo: InMemoryTransactionRepository
    categories_repo: InMemoryCategoryRepository
    budgets_repo: InMemoryBudgetRepository
    rules_repo: InMemoryRuleRepository
    recurring_repo: InMemoryRecurringRepository
    alerts_repo: InMemoryAlertRepository
    channel: RecordingChannel
    observer: RecordingObserver
    monitor: BudgetMonitor
    categorization: CategorizationService
    transactions: TransactionService
    budgets: BudgetService
    categories: CategoryService
    rules: RuleService
    recurring: RecurringService
    reports: ReportService
    alerts: AlertService
    dashboard: DashboardService

    def category(self, name: str, limit: int | None = None) -> Category:
        """Create a category, optionally with a budget."""
        details = self.categories.create(
            CategoryInput(name, "#3b82f6", "tag", Money.of(limit) if limit is not None else None)
        )
        return details.category

    def spend(
        self, amount: str, category: Category | None, on: date | None = None, text: str = "Item"
    ) -> Transaction:
        """Record an expense."""
        return self.transactions.record(
            TransactionInput(
                TransactionType.EXPENSE,
                Money.of(amount),
                text,
                on or self.clock.today(),
                category.id if category else None,
            )
        )


def build_world(today: date = TODAY, thresholds: tuple[int, ...] = (80, 100)) -> World:
    """Wire the application core exactly like the composition root does, but with fakes."""
    clock = FixedClock(today)
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()
    budget_repo = InMemoryBudgetRepository()
    rule_repo = InMemoryRuleRepository()
    rec_repo = InMemoryRecurringRepository()
    alert_repo = InMemoryAlertRepository()

    monitor = BudgetMonitor(
        [PercentageThresholdRule(Decimal(t)) for t in thresholds],
        cat_repo,
        budget_repo,
        tx_repo,
        alert_repo,
        clock,
    )
    channel = RecordingChannel()
    observer = RecordingObserver()
    monitor.attach(NotificationDispatcher([channel]))
    monitor.attach(observer)

    chain = (
        CategorizationChainBuilder()
        .add(KeywordRuleHandler(rule_repo))
        .add(MerchantRuleHandler(DEFAULT_MERCHANTS, cat_repo))
        .add(UserDefinedRuleHandler(tx_repo))
        .add(DefaultCategoryHandler(cat_repo))
        .build()
    )
    categorization = CategorizationService(chain, cat_repo)
    transactions = TransactionService(tx_repo, cat_repo, categorization, monitor)
    budgets = BudgetService(budget_repo, cat_repo, tx_repo, monitor, clock)
    categories = CategoryService(cat_repo, budgets, rule_repo, tx_repo, rec_repo)
    categories.ensure_system_categories()
    recurring = RecurringService(rec_repo, cat_repo, transactions, clock)
    return World(
        clock=clock,
        transactions_repo=tx_repo,
        categories_repo=cat_repo,
        budgets_repo=budget_repo,
        rules_repo=rule_repo,
        recurring_repo=rec_repo,
        alerts_repo=alert_repo,
        channel=channel,
        observer=observer,
        monitor=monitor,
        categorization=categorization,
        transactions=transactions,
        budgets=budgets,
        categories=categories,
        rules=RuleService(rule_repo, cat_repo),
        recurring=recurring,
        reports=ReportService(
            build_report_registry(), RepositoryReportDataSource(tx_repo, cat_repo, budget_repo)
        ),
        alerts=AlertService(alert_repo),
        dashboard=DashboardService(tx_repo, cat_repo, budgets, recurring, clock),
    )


@pytest.fixture
def world() -> World:
    """A fresh application core for each test."""
    return build_world()
