"""Observer pattern: the subject that watches budgets."""

from __future__ import annotations

from collections.abc import Sequence

from app.application.ports import (
    AlertRepository,
    BudgetRepository,
    CategoryRepository,
    Clock,
    TransactionRepository,
)
from app.domain.alert import Alert
from app.domain.alert_observer import AlertObserver
from app.domain.alert_rules import AlertRule
from app.domain.money import Period


class BudgetMonitor:
    """*Subject* of the Observer pattern and *Context* of the AlertRule strategy.

    After any change that can affect spending, services call :meth:`check`.
    The monitor recomputes the category's usage from the source of truth,
    lets every :class:`AlertRule` evaluate it, records each new alert
    atomically (the repository refuses duplicates for the same category,
    month and rule) and then notifies every attached :class:`AlertObserver`.

    Consequences that the design guarantees:

    * one transaction crossing 80% *and* 100% raises both alerts, in rule order;
    * re-checking never re-alerts: each rule fires once per category per month;
    * a new month is a new key, so alert state "resets" without any job;
    * edits, deletes and limit changes are safe because usage is always
      recomputed rather than incrementally tracked.
    """

    def __init__(
        self,
        rules: Sequence[AlertRule],
        categories: CategoryRepository,
        budgets: BudgetRepository,
        transactions: TransactionRepository,
        alerts: AlertRepository,
        clock: Clock,
    ) -> None:
        self._rules = tuple(rules)
        self._categories = categories
        self._budgets = budgets
        self._transactions = transactions
        self._alerts = alerts
        self._clock = clock
        self._observers: list[AlertObserver] = []

    def attach(self, observer: AlertObserver) -> None:
        """Subscribe an observer (idempotent)."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: AlertObserver) -> None:
        """Unsubscribe an observer (no-op when not attached)."""
        if observer in self._observers:
            self._observers.remove(observer)

    def check(self, category_id: str, period: Period) -> list[Alert]:
        """Evaluate every rule for one category and month; return newly raised alerts."""
        budget = self._budgets.get(category_id)
        category = self._categories.get(category_id)
        if budget is None or category is None:
            return []
        usage = budget.usage(
            category_name=category.name,
            period=period,
            spent=self._transactions.expense_total(category_id, period),
        )
        raised: list[Alert] = []
        for rule in self._rules:
            decision = rule.evaluate(usage)
            if decision is None:
                continue
            alert = Alert.create(
                category_id=category_id,
                category_name=category.name,
                period=period,
                rule_key=rule.key,
                level=decision.level,
                threshold=decision.threshold,
                message=decision.message,
                spent=usage.spent,
                limit=usage.limit,
                created_at=self._clock.now(),
            )
            if self._alerts.add_if_absent(alert):
                raised.append(alert)
        for alert in raised:
            self._notify(alert)
        return raised

    def _notify(self, alert: Alert) -> None:
        for observer in list(self._observers):
            observer.on_alert(alert)
