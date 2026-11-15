"""Pydantic request/response schemas.

These are deliberately separate from domain entities: the HTTP contract can
evolve (renamed fields, extra presentation data) without touching business
code, and Pydantic never leaks into the domain. Decimals serialise as JSON
strings so no precision is lost on the wire.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import (
    AlertLevel,
    BudgetHealth,
    CategorySource,
    Frequency,
    TransactionType,
    UserRole,
)

PositiveAmount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class InputModel(BaseModel):
    """Base for request bodies: trims strings and rejects unknown fields."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


# --- Transactions -------------------------------------------------------------


class TransactionIn(InputModel):
    """Create or replace a transaction. Omit ``category_id`` on an expense to auto-categorise."""

    type: TransactionType
    amount: PositiveAmount
    description: str = Field(min_length=1, max_length=200)
    occurred_on: date
    category_id: str | None = None


class TransactionOut(BaseModel):
    """A transaction."""

    id: str
    type: TransactionType
    amount: Decimal
    description: str
    occurred_on: date
    category_id: str | None
    category_source: CategorySource
    recurring_id: str | None


class TransactionPageOut(BaseModel):
    """A page of transactions."""

    items: list[TransactionOut]
    total: int
    page: int
    page_size: int
    pages: int


# --- Categories & budgets -----------------------------------------------------


class CategoryIn(InputModel):
    """Create or update a category. Omit ``monthly_limit`` for no budget."""

    name: str = Field(min_length=1, max_length=50)
    color: HexColor = "#64748b"
    icon: str = Field(default="tag", min_length=1, max_length=40)
    monthly_limit: PositiveAmount | None = None


class CategoryOut(BaseModel):
    """A category with its optional monthly limit."""

    id: str
    name: str
    color: str
    icon: str
    is_system: bool
    monthly_limit: Decimal | None


class BudgetLimitIn(InputModel):
    """Set a category's monthly limit (must be greater than zero)."""

    monthly_limit: PositiveAmount


class BudgetStatusOut(BaseModel):
    """How much of a category's budget is used in a month."""

    category_id: str
    category_name: str
    color: str
    icon: str
    period: str
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: Decimal
    health: BudgetHealth


# --- Rules & categorisation ---------------------------------------------------


class RuleIn(InputModel):
    """A keyword rule."""

    keyword: str = Field(min_length=2, max_length=50)
    category_id: str


class RuleOut(BaseModel):
    """A keyword rule."""

    id: str
    keyword: str
    category_id: str


class SuggestionOut(BaseModel):
    """The category auto-categorisation would choose, and why."""

    category_id: str
    category_name: str
    color: str
    icon: str
    matched_by: str
    reason: str


# --- Recurring payments -------------------------------------------------------


class RecurringIn(InputModel):
    """Create a recurring payment."""

    description: str = Field(min_length=1, max_length=200)
    amount: PositiveAmount
    type: TransactionType = TransactionType.EXPENSE
    frequency: Frequency
    start_date: date
    end_date: date | None = None
    category_id: str | None = None

    @model_validator(mode="after")
    def _end_after_start(self) -> RecurringIn:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class RecurringOut(BaseModel):
    """A recurring payment and its next due date."""

    id: str
    description: str
    amount: Decimal
    type: TransactionType
    frequency: Frequency
    start_date: date
    end_date: date | None
    category_id: str | None
    is_active: bool
    last_generated_on: date | None
    next_due: date | None


class GenerationResultOut(BaseModel):
    """Result of running recurring generation."""

    created: int


# --- Reports ------------------------------------------------------------------


class ReportTypeOut(BaseModel):
    """An available report strategy."""

    key: str
    title: str
    description: str


class ReportColumnOut(BaseModel):
    """A report table column."""

    key: str
    label: str
    kind: str


class ReportMetricOut(BaseModel):
    """A headline figure."""

    label: str
    value: str | int
    kind: str


class ChartSpecOut(BaseModel):
    """Chart hint for the UI."""

    kind: str
    x_key: str
    y_keys: list[str]


class ReportOut(BaseModel):
    """A generated report."""

    key: str
    title: str
    period: str
    columns: list[ReportColumnOut]
    rows: list[dict[str, str | int]]
    metrics: list[ReportMetricOut]
    chart: ChartSpecOut | None


# --- Alerts -------------------------------------------------------------------


class AlertOut(BaseModel):
    """A budget alert."""

    id: str
    category_id: str
    category_name: str
    period: str
    level: AlertLevel
    threshold: Decimal
    message: str
    spent: Decimal
    limit: Decimal
    created_at: datetime
    is_read: bool


class UnreadCountOut(BaseModel):
    """Number of unread alerts."""

    count: int


class MarkAllReadOut(BaseModel):
    """How many alerts were marked read."""

    updated: int


# --- Dashboard ----------------------------------------------------------------


class CategorySpendOut(BaseModel):
    """Spending in one category."""

    category_id: str
    name: str
    color: str
    amount: Decimal


class TrendPointOut(BaseModel):
    """Income and expenses for one month."""

    period: str
    income: Decimal
    expenses: Decimal


class UpcomingPaymentOut(BaseModel):
    """A recurring payment's next occurrence."""

    id: str
    description: str
    amount: Decimal
    type: TransactionType
    frequency: Frequency
    category_id: str | None
    due_on: date


class DashboardOut(BaseModel):
    """Everything the dashboard renders."""

    period: str
    income: Decimal
    expenses: Decimal
    balance: Decimal
    budget_total: Decimal
    budget_spent: Decimal
    budget_used_percent: Decimal
    days_elapsed: int
    days_in_month: int
    spending_by_category: list[CategorySpendOut]
    trend: list[TrendPointOut]
    budgets: list[BudgetStatusOut]
    recent: list[TransactionOut]
    upcoming: list[UpcomingPaymentOut]


# --- Errors -------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """One field-level problem."""

    field: str
    message: str


class ErrorBody(BaseModel):
    """Error payload."""

    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorOut(BaseModel):
    """Consistent error envelope returned by every failing endpoint."""

    error: ErrorBody


# --- Accounts -----------------------------------------------------------------

EmailField = Annotated[
    str, Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
]


class RegisterIn(InputModel):
    """Create an account."""

    name: str = Field(min_length=1, max_length=60)
    email: EmailField
    password: str = Field(min_length=8, max_length=128)


class LoginIn(InputModel):
    """Sign in."""

    email: EmailField
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    """A user account (never includes the password hash)."""

    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class AuthOut(BaseModel):
    """A session: bearer token plus the signed-in user."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DemoAccountOut(BaseModel):
    """A ready-made demo login shown on the sign-in page."""

    name: str
    email: str
    password: str
    role: UserRole
    tagline: str


# --- Admin --------------------------------------------------------------------


class DailyCountOut(BaseModel):
    """A count for one day."""

    day: date
    count: int


class PlatformOverviewOut(BaseModel):
    """Headline platform statistics."""

    total_users: int
    active_users: int
    admins: int
    new_users_7d: int
    transactions: int
    expense_volume: Decimal
    alerts_30d: int
    signups_by_day: list[DailyCountOut]
    activity_by_day: list[DailyCountOut]


class AdminUserOut(UserOut):
    """A user with activity counts, for administrators."""

    transaction_count: int
    category_count: int
    last_transaction_on: date | None


class AdminUserUpdateIn(InputModel):
    """Change a user's status and/or role."""

    is_active: bool | None = None
    role: UserRole | None = None
