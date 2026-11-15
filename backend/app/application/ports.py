"""Ports: the abstractions the application layer depends on (Dependency Inversion).

Repositories and the clock are ``typing.Protocol`` classes: adapters satisfy
them structurally, without inheriting, which keeps infrastructure decoupled
and makes in-memory fakes trivial. ``NotificationChannel`` is an ``abc.ABC``
because it is a pattern participant that concrete channels explicitly
extend; ABCs also fail fast at instantiation if a method is missing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import ClassVar, Protocol

from app.application.queries import Page, TransactionQuery
from app.domain.alert import Alert
from app.domain.budget import Budget
from app.domain.category import Category
from app.domain.category_rule import CategoryRule
from app.domain.enums import UserRole
from app.domain.money import Money, Period
from app.domain.recurrence import RecurringPayment
from app.domain.transaction import Transaction
from app.domain.user import User


class Clock(Protocol):
    """Source of the current time; injected so tests can freeze or move time."""

    def today(self) -> date:
        """The current local date."""
        ...

    def now(self) -> datetime:
        """The current timezone-aware timestamp."""
        ...


class TransactionRepository(Protocol):
    """Persistence port for transactions."""

    def add(self, transaction: Transaction) -> None:
        """Store a new transaction; raise ``DuplicateRecurrenceError`` on a repeat occurrence."""
        ...

    def update(self, transaction: Transaction) -> None:
        """Replace an existing transaction."""
        ...

    def delete(self, transaction_id: str) -> None:
        """Remove a transaction."""
        ...

    def get(self, transaction_id: str) -> Transaction | None:
        """Fetch one transaction."""
        ...

    def search(self, query: TransactionQuery) -> Page[Transaction]:
        """Filtered, sorted, paginated listing."""
        ...

    def list_between(self, start: date, end: date) -> list[Transaction]:
        """All transactions with ``start <= occurred_on <= end``."""
        ...

    def recent(self, limit: int) -> list[Transaction]:
        """The most recent transactions."""
        ...

    def expense_total(self, category_id: str, period: Period) -> Money:
        """Total expenses for a category in a month."""
        ...

    def exists_for_recurrence(self, recurring_id: str, occurred_on: date) -> bool:
        """Whether an occurrence of a recurring payment was already generated."""
        ...

    def latest_manual_category_for(self, normalized_description: str) -> str | None:
        """Category id most recently chosen by hand for this description."""
        ...

    def reassign_category(self, from_category_id: str, to_category_id: str) -> int:
        """Move every transaction of one category to another; return how many moved."""
        ...

    def count(self) -> int:
        """Number of stored transactions."""
        ...


class CategoryRepository(Protocol):
    """Persistence port for categories."""

    def add(self, category: Category) -> None:
        """Store a new category."""
        ...

    def update(self, category: Category) -> None:
        """Replace an existing category."""
        ...

    def delete(self, category_id: str) -> None:
        """Remove a category."""
        ...

    def get(self, category_id: str) -> Category | None:
        """Fetch one category."""
        ...

    def list_all(self) -> list[Category]:
        """All categories."""
        ...

    def find_by_name(self, name: str) -> Category | None:
        """Case-insensitive lookup by name."""
        ...


class BudgetRepository(Protocol):
    """Persistence port for budgets (one per category)."""

    def get(self, category_id: str) -> Budget | None:
        """The budget of a category, if any."""
        ...

    def save(self, budget: Budget) -> None:
        """Insert or replace a category's budget."""
        ...

    def delete(self, category_id: str) -> None:
        """Remove a category's budget (no-op when absent)."""
        ...

    def list_all(self) -> list[Budget]:
        """All budgets."""
        ...


class CategoryRuleRepository(Protocol):
    """Persistence port for keyword rules."""

    def add(self, rule: CategoryRule) -> None:
        """Store a new rule."""
        ...

    def update(self, rule: CategoryRule) -> None:
        """Replace an existing rule."""
        ...

    def delete(self, rule_id: str) -> None:
        """Remove a rule."""
        ...

    def get(self, rule_id: str) -> CategoryRule | None:
        """Fetch one rule."""
        ...

    def list_rules(self) -> list[CategoryRule]:
        """All rules."""
        ...

    def find_by_keyword(self, keyword: str) -> CategoryRule | None:
        """Lookup by normalised keyword."""
        ...

    def delete_for_category(self, category_id: str) -> None:
        """Remove every rule pointing at a category."""
        ...


class RecurringPaymentRepository(Protocol):
    """Persistence port for recurring payments."""

    def add(self, payment: RecurringPayment) -> None:
        """Store a new recurring payment."""
        ...

    def update(self, payment: RecurringPayment) -> None:
        """Replace an existing recurring payment."""
        ...

    def mark_generated(self, recurring_id: str, through: date) -> None:
        """Advance only the generation mark (never overwrites pause/resume)."""
        ...

    def delete(self, recurring_id: str) -> None:
        """Remove a recurring payment."""
        ...

    def get(self, recurring_id: str) -> RecurringPayment | None:
        """Fetch one recurring payment."""
        ...

    def list_all(self) -> list[RecurringPayment]:
        """All recurring payments."""
        ...

    def reassign_category(self, from_category_id: str, to_category_id: str) -> None:
        """Point recurring payments at another category."""
        ...


class AlertRepository(Protocol):
    """Persistence port for alert history."""

    def add_if_absent(self, alert: Alert) -> bool:
        """Store the alert unless one exists for the same (category, period, rule).

        Returns True when stored. This atomic check is what guarantees each
        threshold fires once per category per month.
        """
        ...

    def list_recent(self, limit: int, unread_only: bool) -> list[Alert]:
        """Newest alerts first."""
        ...

    def mark_read(self, alert_id: str) -> bool:
        """Flag one alert as read; False when it does not exist."""
        ...

    def mark_all_read(self) -> int:
        """Flag every alert as read; return how many changed."""
        ...

    def unread_count(self) -> int:
        """Number of unread alerts."""
        ...


class NotificationChannel(ABC):
    """Strategy-style extension point for delivering alerts (console, e-mail, SMS, in-app).

    Add a channel by subclassing and registering it in the composition root;
    nothing else changes (Open/Closed).
    """

    name: ClassVar[str]

    @abstractmethod
    def send(self, alert: Alert) -> None:
        """Deliver the alert. Implementations may raise; the dispatcher isolates failures."""


# --- Accounts and administration -------------------------------------------------


class UserRepository(Protocol):
    """Persistence port for accounts (not owner-scoped)."""

    def add(self, user: User) -> None:
        """Store a new user; raise ``ConflictError`` if the e-mail is taken."""
        ...

    def update(self, user: User) -> None:
        """Replace an existing user."""
        ...

    def get(self, user_id: str) -> User | None:
        """Fetch one user."""
        ...

    def get_by_email(self, email: str) -> User | None:
        """Case-insensitive look-up by e-mail."""
        ...

    def list_all(self) -> list[User]:
        """Every user."""
        ...

    def count(self) -> int:
        """Number of users."""
        ...


class PasswordHasher(Protocol):
    """One-way password hashing (implemented with scrypt in infrastructure)."""

    def hash(self, password: str) -> str:
        """Return a salted hash suitable for storage."""
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        """Constant-time check of a password against a stored hash."""
        ...


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """What a verified session token says about its bearer."""

    user_id: str
    role: UserRole
    expires_at: datetime


class TokenIssuer(Protocol):
    """Issues and verifies signed session tokens (JWT in infrastructure)."""

    def issue(self, user: User) -> str:
        """Create a signed token for ``user``."""
        ...

    def verify(self, token: str) -> TokenClaims | None:
        """Return the claims of a valid token, or None if invalid or expired."""
        ...


@dataclass(frozen=True, slots=True)
class UserActivity:
    """How much one user has done, for the admin user list."""

    transaction_count: int
    category_count: int
    last_transaction_on: date | None


class PlatformStatsReader(Protocol):
    """Cross-user, read-only statistics for administrators."""

    def transaction_count(self) -> int:
        """Transactions across all users."""
        ...

    def expense_volume(self) -> Money:
        """Total expenses tracked across all users."""
        ...

    def alerts_since(self, since: datetime) -> int:
        """Alerts raised since a moment."""
        ...

    def activity_by_user(self) -> dict[str, UserActivity]:
        """Per-user activity keyed by user id."""
        ...

    def transactions_by_day(self, since: date) -> dict[date, int]:
        """Number of transactions per day since a date."""
        ...
