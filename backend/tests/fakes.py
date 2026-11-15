"""In-memory fakes for every port.

They satisfy the repository Protocols structurally, which is itself a
demonstration of Dependency Inversion: services run unchanged against
dictionaries in tests and SQLAlchemy in production.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta

from app.application.ports import NotificationChannel, UserActivity
from app.application.queries import Page, SortDirection, SortField, TransactionQuery
from app.domain.alert import Alert
from app.domain.alert_observer import AlertObserver
from app.domain.budget import Budget
from app.domain.category import Category
from app.domain.category_rule import CategoryRule
from app.domain.enums import CategorySource
from app.domain.errors import ConflictError, DuplicateRecurrenceError, NotFoundError
from app.domain.money import Money, Period
from app.domain.recurrence import RecurringPayment
from app.domain.transaction import Transaction, normalize_description
from app.domain.user import User


class FixedClock:
    """A clock whose date only moves when the test says so."""

    def __init__(self, today: date) -> None:
        self.current = today

    def today(self) -> date:
        return self.current

    def now(self) -> datetime:
        return datetime.combine(self.current, time(12), tzinfo=UTC)

    def advance(self, days: int) -> None:
        self.current += timedelta(days=days)


class InMemoryTransactionRepository:
    def __init__(self) -> None:
        self.items: dict[str, Transaction] = {}
        self._order: dict[str, int] = {}

    def add(self, transaction: Transaction) -> None:
        if transaction.recurring_id and self.exists_for_recurrence(
            transaction.recurring_id, transaction.occurred_on
        ):
            raise DuplicateRecurrenceError("duplicate")
        self.items[transaction.id] = transaction
        self._order[transaction.id] = len(self._order)

    def update(self, transaction: Transaction) -> None:
        if transaction.id not in self.items:
            raise NotFoundError("Transaction", transaction.id)
        self.items[transaction.id] = transaction

    def delete(self, transaction_id: str) -> None:
        self.items.pop(transaction_id, None)

    def get(self, transaction_id: str) -> Transaction | None:
        return self.items.get(transaction_id)

    def search(self, query: TransactionQuery) -> Page[Transaction]:
        rows = list(self.items.values())
        if query.type:
            rows = [t for t in rows if t.type is query.type]
        if query.category_id:
            rows = [t for t in rows if t.category_id == query.category_id]
        if query.search:
            term = normalize_description(query.search)
            rows = [t for t in rows if term in normalize_description(t.description)]
        if query.date_from:
            rows = [t for t in rows if t.occurred_on >= query.date_from]
        if query.date_to:
            rows = [t for t in rows if t.occurred_on <= query.date_to]
        keys = {
            SortField.OCCURRED_ON: lambda t: t.occurred_on,
            SortField.AMOUNT: lambda t: t.amount.amount,
            SortField.DESCRIPTION: lambda t: t.description.lower(),
        }
        rows.sort(key=keys[query.sort_by], reverse=query.sort_direction is SortDirection.DESC)
        window = rows[query.offset : query.offset + query.page_size]
        return Page(window, len(rows), query.page, query.page_size)

    def list_between(self, start: date, end: date) -> list[Transaction]:
        return sorted(
            (t for t in self.items.values() if start <= t.occurred_on <= end),
            key=lambda t: t.occurred_on,
        )

    def recent(self, limit: int) -> list[Transaction]:
        rows = sorted(
            self.items.values(), key=lambda t: (t.occurred_on, self._order[t.id]), reverse=True
        )
        return rows[:limit]

    def expense_total(self, category_id: str, period: Period) -> Money:
        total = Money.zero()
        for t in self.items.values():
            if t.is_expense and t.category_id == category_id and period.contains(t.occurred_on):
                total = total + t.amount
        return total

    def exists_for_recurrence(self, recurring_id: str, occurred_on: date) -> bool:
        return any(
            t.recurring_id == recurring_id and t.occurred_on == occurred_on
            for t in self.items.values()
        )

    def latest_manual_category_for(self, normalized_description: str) -> str | None:
        matches = [
            t
            for t in self.items.values()
            if normalize_description(t.description) == normalized_description
            and t.category_source is CategorySource.MANUAL
            and t.category_id
        ]
        if not matches:
            return None
        return max(matches, key=lambda t: (t.occurred_on, self._order[t.id])).category_id

    def reassign_category(self, from_category_id: str, to_category_id: str) -> int:
        moved = 0
        for key, t in list(self.items.items()):
            if t.category_id == from_category_id:
                self.items[key] = replace(t, category_id=to_category_id)
                moved += 1
        return moved

    def count(self) -> int:
        return len(self.items)


class InMemoryCategoryRepository:
    def __init__(self) -> None:
        self.items: dict[str, Category] = {}

    def add(self, category: Category) -> None:
        if self.find_by_name(category.name):
            raise ConflictError("duplicate")
        self.items[category.id] = category

    def update(self, category: Category) -> None:
        self.items[category.id] = category

    def delete(self, category_id: str) -> None:
        self.items.pop(category_id, None)

    def get(self, category_id: str) -> Category | None:
        return self.items.get(category_id)

    def list_all(self) -> list[Category]:
        return list(self.items.values())

    def find_by_name(self, name: str) -> Category | None:
        key = " ".join(name.split()).lower()
        return next((c for c in self.items.values() if c.name.lower() == key), None)


class InMemoryBudgetRepository:
    def __init__(self) -> None:
        self.items: dict[str, Budget] = {}

    def get(self, category_id: str) -> Budget | None:
        return self.items.get(category_id)

    def save(self, budget: Budget) -> None:
        self.items[budget.category_id] = budget

    def delete(self, category_id: str) -> None:
        self.items.pop(category_id, None)

    def list_all(self) -> list[Budget]:
        return list(self.items.values())


class InMemoryRuleRepository:
    def __init__(self) -> None:
        self.items: dict[str, CategoryRule] = {}

    def add(self, rule: CategoryRule) -> None:
        self.items[rule.id] = rule

    def update(self, rule: CategoryRule) -> None:
        self.items[rule.id] = rule

    def delete(self, rule_id: str) -> None:
        self.items.pop(rule_id, None)

    def get(self, rule_id: str) -> CategoryRule | None:
        return self.items.get(rule_id)

    def list_rules(self) -> list[CategoryRule]:
        return list(self.items.values())

    def find_by_keyword(self, keyword: str) -> CategoryRule | None:
        key = " ".join(keyword.split()).lower()
        return next((r for r in self.items.values() if r.keyword == key), None)

    def delete_for_category(self, category_id: str) -> None:
        for key in [k for k, r in self.items.items() if r.category_id == category_id]:
            del self.items[key]


class InMemoryRecurringRepository:
    def __init__(self) -> None:
        self.items: dict[str, RecurringPayment] = {}

    def add(self, payment: RecurringPayment) -> None:
        self.items[payment.id] = payment

    def update(self, payment: RecurringPayment) -> None:
        self.items[payment.id] = payment

    def mark_generated(self, recurring_id: str, through: date) -> None:
        self.items[recurring_id] = self.items[recurring_id].generated_through(through)

    def delete(self, recurring_id: str) -> None:
        self.items.pop(recurring_id, None)

    def get(self, recurring_id: str) -> RecurringPayment | None:
        return self.items.get(recurring_id)

    def list_all(self) -> list[RecurringPayment]:
        return list(self.items.values())

    def reassign_category(self, from_category_id: str, to_category_id: str) -> None:
        for key, p in list(self.items.items()):
            if p.category_id == from_category_id:
                self.items[key] = replace(p, category_id=to_category_id)


class InMemoryAlertRepository:
    def __init__(self) -> None:
        self.items: dict[str, Alert] = {}

    def add_if_absent(self, alert: Alert) -> bool:
        key = (alert.category_id, alert.period, alert.rule_key)
        if any((a.category_id, a.period, a.rule_key) == key for a in self.items.values()):
            return False
        self.items[alert.id] = alert
        return True

    def list_recent(self, limit: int, unread_only: bool) -> list[Alert]:
        rows = [a for a in self.items.values() if not (unread_only and a.is_read)]
        return list(reversed(rows))[:limit]

    def mark_read(self, alert_id: str) -> bool:
        if alert_id not in self.items:
            return False
        self.items[alert_id] = self.items[alert_id].mark_read()
        return True

    def mark_all_read(self) -> int:
        unread = [a for a in self.items.values() if not a.is_read]
        for alert in unread:
            self.items[alert.id] = alert.mark_read()
        return len(unread)

    def unread_count(self) -> int:
        return sum(not a.is_read for a in self.items.values())


class RecordingChannel(NotificationChannel):
    """Captures alerts instead of delivering them."""

    name = "recording"

    def __init__(self) -> None:
        self.sent: list[Alert] = []

    def send(self, alert: Alert) -> None:
        self.sent.append(alert)


class FailingChannel(NotificationChannel):
    """Always raises, to prove failures are isolated."""

    name = "failing"

    def send(self, alert: Alert) -> None:
        raise RuntimeError("SMTP server unreachable")


class RecordingObserver(AlertObserver):
    """Captures alerts the subject publishes."""

    def __init__(self) -> None:
        self.received: list[Alert] = []

    def on_alert(self, alert: Alert) -> None:
        self.received.append(alert)


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    def add(self, user: User) -> None:
        if self.get_by_email(user.email):
            raise ConflictError("duplicate")
        self.items[user.id] = user

    def update(self, user: User) -> None:
        self.items[user.id] = user

    def get(self, user_id: str) -> User | None:
        return self.items.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.items.values() if u.email == email.strip().lower()), None)

    def list_all(self) -> list[User]:
        return list(self.items.values())

    def count(self) -> int:
        return len(self.items)


class FastHasher:
    """Deterministic stand-in for scrypt so auth tests stay fast."""

    def hash(self, password: str) -> str:
        return f"fake${password[::-1]}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == self.hash(password)


class InMemoryPlatformStats:
    def __init__(self, activity: dict[str, UserActivity] | None = None) -> None:
        self.activity = activity or {}

    def transaction_count(self) -> int:
        return sum(a.transaction_count for a in self.activity.values())

    def expense_volume(self) -> Money:
        return Money.of(1234)

    def alerts_since(self, since: datetime) -> int:
        return 3

    def activity_by_user(self) -> dict[str, UserActivity]:
        return self.activity

    def transactions_by_day(self, since: date) -> dict[date, int]:
        return {since: 2}
