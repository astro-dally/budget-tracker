"""Composition root: the single place where concrete classes are chosen and wired.

Two levels of wiring:

* :class:`Container` holds application-wide objects built once at start-up
  (engine, SSE hub, auth, admin, scheduler, report registry).
* :class:`UserScope` is the per-user graph of use-case services, built for
  the signed-in user on each request. Its repositories are bound to that
  user's id, so services never filter by user themselves and *cannot* reach
  another user's data. The services are unchanged from the single-user
  design; only their wiring is scoped (Dependency Inversion paying off).

Adding a notification channel, alert rule, report or categorisation handler
means writing the new class and registering it here; no business class
changes (Open/Closed).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.admin_service import AdminService
from app.application.alert_service import AlertService
from app.application.auth_service import AuthService, LoginThrottle
from app.application.budget_monitor import BudgetMonitor
from app.application.budget_service import BudgetService
from app.application.categorization_service import CategorizationService
from app.application.category_service import CategoryService
from app.application.dashboard_service import DashboardService
from app.application.observers import NotificationDispatcher
from app.application.onboarding import StarterKit
from app.application.ports import Clock, NotificationChannel
from app.application.recurring_service import RecurringService
from app.application.report_service import ReportService, RepositoryReportDataSource
from app.application.rule_service import RuleService
from app.application.transaction_service import TransactionService
from app.config import Settings
from app.domain.alert_rules import AlertRule, PercentageThresholdRule
from app.domain.categorization import (
    CategorizationChainBuilder,
    CategorizationHandler,
    DefaultCategoryHandler,
    KeywordRuleHandler,
    MerchantRuleHandler,
    UserDefinedRuleHandler,
)
from app.domain.reports import (
    CategoryWiseReport,
    MonthlySummaryReport,
    ReportRegistry,
    SpendingTrendReport,
)
from app.domain.user import User
from app.infrastructure.clock import SystemClock
from app.infrastructure.merchant_directory import DEFAULT_MERCHANTS
from app.infrastructure.notifications import (
    ConsoleChannel,
    EmailChannel,
    EmailSettings,
    InAppChannel,
    SmsChannel,
)
from app.infrastructure.persistence.database import create_db_engine, create_session_factory
from app.infrastructure.persistence.platform_stats import SqlAlchemyPlatformStats
from app.infrastructure.persistence.repositories import (
    SqlAlchemyAlertRepository,
    SqlAlchemyBudgetRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCategoryRuleRepository,
    SqlAlchemyRecurringPaymentRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.realtime import AlertBroadcaster
from app.infrastructure.scheduler import RecurringTransactionScheduler
from app.infrastructure.security import JwtTokenIssuer, ScryptPasswordHasher


@dataclass(slots=True)
class Repositories:
    """All repository adapters for one user, built from one session factory."""

    transactions: SqlAlchemyTransactionRepository
    categories: SqlAlchemyCategoryRepository
    budgets: SqlAlchemyBudgetRepository
    rules: SqlAlchemyCategoryRuleRepository
    recurring: SqlAlchemyRecurringPaymentRepository
    alerts: SqlAlchemyAlertRepository

    @classmethod
    def build(cls, sessions: sessionmaker[Session], owner_id: str) -> Repositories:
        """Create every repository bound to ``owner_id``."""
        return cls(
            transactions=SqlAlchemyTransactionRepository(sessions, owner_id),
            categories=SqlAlchemyCategoryRepository(sessions, owner_id),
            budgets=SqlAlchemyBudgetRepository(sessions, owner_id),
            rules=SqlAlchemyCategoryRuleRepository(sessions, owner_id),
            recurring=SqlAlchemyRecurringPaymentRepository(sessions, owner_id),
            alerts=SqlAlchemyAlertRepository(sessions, owner_id),
        )


@dataclass(slots=True)
class UserScope:
    """The signed-in user's services."""

    user: User
    repositories: Repositories
    monitor: BudgetMonitor
    dispatcher: NotificationDispatcher
    categorization: CategorizationService
    transactions: TransactionService
    budgets: BudgetService
    categories: CategoryService
    rules: RuleService
    recurring: RecurringService
    reports: ReportService
    alerts: AlertService
    dashboard: DashboardService


@dataclass(slots=True)
class Container:
    """Application-wide objects, held on ``app.state``."""

    settings: Settings
    clock: Clock
    engine: Engine
    sessions: sessionmaker[Session]
    broadcaster: AlertBroadcaster
    report_registry: ReportRegistry
    users: SqlAlchemyUserRepository
    auth: AuthService
    admin: AdminService
    scheduler: RecurringTransactionScheduler = field(init=False)

    def __post_init__(self) -> None:
        self.scheduler = RecurringTransactionScheduler(
            self.generate_recurring_for_all_users, self.settings.recurring_job_interval_minutes
        )

    def scope_for(self, user: User) -> UserScope:
        """Wire the per-user service graph."""
        return build_user_scope(
            user, self.settings, self.clock, self.sessions, self.broadcaster, self.report_registry
        )

    def generate_recurring_for_all_users(self) -> int:
        """Scheduler job: generate due recurring transactions for every active user."""
        return sum(
            self.scope_for(user).recurring.generate_due()
            for user in self.users.list_all()
            if user.is_active
        )

    def close(self) -> None:
        """Release background threads and database connections."""
        self.scheduler.shutdown()
        self.engine.dispose()


def build_alert_rules(settings: Settings) -> list[AlertRule]:
    """One percentage rule per configured threshold, ascending."""
    return [PercentageThresholdRule(threshold) for threshold in settings.alert_threshold_list]


def build_channels(
    settings: Settings, broadcaster: AlertBroadcaster, user: User
) -> list[NotificationChannel]:
    """Instantiate the enabled notification channels for one user."""
    factories: dict[str, Callable[[], NotificationChannel]] = {
        ConsoleChannel.name: ConsoleChannel,
        InAppChannel.name: lambda: InAppChannel(broadcaster, user.id),
        EmailChannel.name: lambda: EmailChannel(
            EmailSettings(
                sender=settings.alert_email_from,
                recipient=user.email,
                host=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
            )
        ),
        SmsChannel.name: lambda: SmsChannel(settings.alert_sms_to),
    }
    return [
        _create(factories, name, "notification channel")()
        for name in settings.notification_channel_list
    ]


def build_categorization_chain(
    order: Sequence[str], repositories: Repositories
) -> CategorizationHandler:
    """Build the Chain of Responsibility in the configured order."""
    factories: dict[str, Callable[[], CategorizationHandler]] = {
        KeywordRuleHandler.name: lambda: KeywordRuleHandler(repositories.rules),
        MerchantRuleHandler.name: lambda: MerchantRuleHandler(
            DEFAULT_MERCHANTS, repositories.categories
        ),
        UserDefinedRuleHandler.name: lambda: UserDefinedRuleHandler(repositories.transactions),
        DefaultCategoryHandler.name: lambda: DefaultCategoryHandler(repositories.categories),
    }
    builder = CategorizationChainBuilder()
    for name in order:
        builder.add(_create(factories, name, "categorisation handler")())
    return builder.build()


def build_report_registry() -> ReportRegistry:
    """Register every report strategy."""
    return (
        ReportRegistry()
        .register(MonthlySummaryReport())
        .register(CategoryWiseReport())
        .register(SpendingTrendReport())
    )


def _create[T](factories: dict[str, Callable[[], T]], name: str, kind: str) -> Callable[[], T]:
    try:
        return factories[name]
    except KeyError:
        known = ", ".join(sorted(factories))
        raise ValueError(f"Unknown {kind} '{name}'. Known values: {known}") from None


def build_user_scope(
    user: User,
    settings: Settings,
    clock: Clock,
    sessions: sessionmaker[Session],
    broadcaster: AlertBroadcaster,
    registry: ReportRegistry,
) -> UserScope:
    """Wire one user's services against repositories bound to that user."""
    repos = Repositories.build(sessions, user.id)
    monitor = BudgetMonitor(
        build_alert_rules(settings),
        repos.categories,
        repos.budgets,
        repos.transactions,
        repos.alerts,
        clock,
    )
    dispatcher = NotificationDispatcher(build_channels(settings, broadcaster, user))
    monitor.attach(dispatcher)
    categorization = CategorizationService(
        build_categorization_chain(settings.categorization_order_list, repos), repos.categories
    )
    transactions = TransactionService(repos.transactions, repos.categories, categorization, monitor)
    budgets = BudgetService(repos.budgets, repos.categories, repos.transactions, monitor, clock)
    recurring = RecurringService(repos.recurring, repos.categories, transactions, clock)
    return UserScope(
        user=user,
        repositories=repos,
        monitor=monitor,
        dispatcher=dispatcher,
        categorization=categorization,
        transactions=transactions,
        budgets=budgets,
        categories=CategoryService(
            repos.categories, budgets, repos.rules, repos.transactions, repos.recurring
        ),
        rules=RuleService(repos.rules, repos.categories),
        recurring=recurring,
        reports=ReportService(
            registry,
            RepositoryReportDataSource(repos.transactions, repos.categories, repos.budgets),
        ),
        alerts=AlertService(repos.alerts),
        dashboard=DashboardService(repos.transactions, repos.categories, budgets, recurring, clock),
    )


def build_container(settings: Settings, clock: Clock | None = None) -> Container:
    """Wire the whole application."""
    clock = clock or SystemClock()
    engine = create_db_engine(settings.database_url)
    sessions = create_session_factory(engine)
    broadcaster = AlertBroadcaster()
    registry = build_report_registry()
    users = SqlAlchemyUserRepository(sessions)

    def onboard(user: User) -> None:
        scope = build_user_scope(user, settings, clock, sessions, broadcaster, registry)
        StarterKit().apply(scope.categories, scope.rules)

    auth = AuthService(
        users,
        ScryptPasswordHasher(),
        JwtTokenIssuer(settings.jwt_secret, clock, timedelta(hours=settings.token_lifetime_hours)),
        clock,
        LoginThrottle(clock),
        on_register=onboard,
    )
    return Container(
        settings=settings,
        clock=clock,
        engine=engine,
        sessions=sessions,
        broadcaster=broadcaster,
        report_registry=registry,
        users=users,
        auth=auth,
        admin=AdminService(users, SqlAlchemyPlatformStats(sessions), clock),
    )
