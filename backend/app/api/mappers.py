"""Translate domain objects into API schemas (one direction, no logic)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.api import schemas
from app.application.admin_service import PlatformOverview, UserSummary
from app.application.budget_service import BudgetStatus
from app.application.categorization_service import CategorySuggestion
from app.application.category_service import CategoryDetails
from app.application.dashboard_service import DashboardOverview
from app.application.queries import Page
from app.application.recurring_service import UpcomingPayment
from app.domain.alert import Alert
from app.domain.category_rule import CategoryRule
from app.domain.recurrence import RecurringPayment
from app.domain.reports import CellValue, Report, ReportStrategy
from app.domain.transaction import Transaction
from app.domain.user import User


def transaction(tx: Transaction) -> schemas.TransactionOut:
    """Map a transaction."""
    return schemas.TransactionOut(
        id=tx.id,
        type=tx.type,
        amount=tx.amount.amount,
        description=tx.description,
        occurred_on=tx.occurred_on,
        category_id=tx.category_id,
        category_source=tx.category_source,
        recurring_id=tx.recurring_id,
    )


def transaction_page(page: Page[Transaction]) -> schemas.TransactionPageOut:
    """Map a page of transactions."""
    return schemas.TransactionPageOut(
        items=[transaction(tx) for tx in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
        pages=page.pages,
    )


def category(details: CategoryDetails) -> schemas.CategoryOut:
    """Map a category with its budget."""
    c = details.category
    return schemas.CategoryOut(
        id=c.id,
        name=c.name,
        color=c.color,
        icon=c.icon,
        is_system=c.is_system,
        monthly_limit=details.budget.monthly_limit.amount if details.budget else None,
    )


def budget_status(status: BudgetStatus) -> schemas.BudgetStatusOut:
    """Map a budget status."""
    usage = status.usage
    return schemas.BudgetStatusOut(
        category_id=status.category.id,
        category_name=status.category.name,
        color=status.category.color,
        icon=status.category.icon,
        period=str(usage.period),
        limit=usage.limit.amount,
        spent=usage.spent.amount,
        remaining=usage.remaining.amount,
        percent_used=usage.percent_used,
        health=usage.health,
    )


def rule(r: CategoryRule) -> schemas.RuleOut:
    """Map a keyword rule."""
    return schemas.RuleOut(id=r.id, keyword=r.keyword, category_id=r.category_id)


def suggestion(s: CategorySuggestion) -> schemas.SuggestionOut:
    """Map a categorisation suggestion."""
    return schemas.SuggestionOut(
        category_id=s.category.id,
        category_name=s.category.name,
        color=s.category.color,
        icon=s.category.icon,
        matched_by=s.matched_by,
        reason=s.reason,
    )


def recurring(payment: RecurringPayment, next_due: date | None) -> schemas.RecurringOut:
    """Map a recurring payment together with its next due date."""
    return schemas.RecurringOut(
        id=payment.id,
        description=payment.description,
        amount=payment.amount.amount,
        type=payment.type,
        frequency=payment.schedule.frequency,
        start_date=payment.schedule.start_date,
        end_date=payment.schedule.end_date,
        category_id=payment.category_id,
        is_active=payment.is_active,
        last_generated_on=payment.last_generated_on,
        next_due=next_due,
    )


def report_type(strategy: ReportStrategy) -> schemas.ReportTypeOut:
    """Map a report strategy's metadata."""
    return schemas.ReportTypeOut(
        key=strategy.key, title=strategy.title, description=strategy.description
    )


def _cell(value: CellValue) -> str | int:
    return str(value) if isinstance(value, Decimal) else value


def report(r: Report) -> schemas.ReportOut:
    """Map a generated report."""
    return schemas.ReportOut(
        key=r.key,
        title=r.title,
        period=str(r.period),
        columns=[
            schemas.ReportColumnOut(key=c.key, label=c.label, kind=c.kind.value) for c in r.columns
        ],
        rows=[{key: _cell(value) for key, value in row.items()} for row in r.rows],
        metrics=[
            schemas.ReportMetricOut(label=m.label, value=_cell(m.value), kind=m.kind.value)
            for m in r.metrics
        ],
        chart=(
            schemas.ChartSpecOut(
                kind=r.chart.kind.value, x_key=r.chart.x_key, y_keys=list(r.chart.y_keys)
            )
            if r.chart
            else None
        ),
    )


def alert(a: Alert) -> schemas.AlertOut:
    """Map an alert."""
    return schemas.AlertOut(
        id=a.id,
        category_id=a.category_id,
        category_name=a.category_name,
        period=str(a.period),
        level=a.level,
        threshold=a.threshold,
        message=a.message,
        spent=a.spent.amount,
        limit=a.limit.amount,
        created_at=a.created_at,
        is_read=a.is_read,
    )


def upcoming(item: UpcomingPayment) -> schemas.UpcomingPaymentOut:
    """Map an upcoming recurring payment."""
    p = item.payment
    return schemas.UpcomingPaymentOut(
        id=p.id,
        description=p.description,
        amount=p.amount.amount,
        type=p.type,
        frequency=p.schedule.frequency,
        category_id=p.category_id,
        due_on=item.due_on,
    )


def dashboard(d: DashboardOverview) -> schemas.DashboardOut:
    """Map the dashboard read model."""
    return schemas.DashboardOut(
        period=str(d.period),
        income=d.income.amount,
        expenses=d.expenses.amount,
        balance=d.balance.amount,
        budget_total=d.budget_total.amount,
        budget_spent=d.budget_spent.amount,
        budget_used_percent=d.budget_used_percent,
        days_elapsed=d.days_elapsed,
        days_in_month=d.days_in_month,
        spending_by_category=[
            schemas.CategorySpendOut(
                category_id=s.category.id,
                name=s.category.name,
                color=s.category.color,
                amount=s.amount.amount,
            )
            for s in d.spending_by_category
        ],
        trend=[
            schemas.TrendPointOut(
                period=str(t.period), income=t.income.amount, expenses=t.expenses.amount
            )
            for t in d.trend
        ],
        budgets=[budget_status(s) for s in d.budgets],
        recent=[transaction(tx) for tx in d.recent],
        upcoming=[upcoming(u) for u in d.upcoming],
    )


def user(u: User) -> schemas.UserOut:
    """Map a user (the password hash is never exposed)."""
    return schemas.UserOut(
        id=u.id,
        email=u.email,
        name=u.name,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at,
        last_login_at=u.last_login_at,
    )


def admin_user(summary: UserSummary) -> schemas.AdminUserOut:
    """Map a user with activity counts."""
    u, activity = summary.user, summary.activity
    return schemas.AdminUserOut(
        **user(u).model_dump(),
        transaction_count=activity.transaction_count,
        category_count=activity.category_count,
        last_transaction_on=activity.last_transaction_on,
    )


def platform_overview(o: PlatformOverview) -> schemas.PlatformOverviewOut:
    """Map platform statistics."""
    return schemas.PlatformOverviewOut(
        total_users=o.total_users,
        active_users=o.active_users,
        admins=o.admins,
        new_users_7d=o.new_users_7d,
        transactions=o.transactions,
        expense_volume=o.expense_volume.amount,
        alerts_30d=o.alerts_30d,
        signups_by_day=[schemas.DailyCountOut(day=d.day, count=d.count) for d in o.signups_by_day],
        activity_by_day=[
            schemas.DailyCountOut(day=d.day, count=d.count) for d in o.activity_by_day
        ],
    )
