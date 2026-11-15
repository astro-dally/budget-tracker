"""The three worked examples from docs/EXTENDING.md, verified.

Each class below is copied verbatim into the docs. None of them required
editing an existing class: they plug in through the AlertRule,
ReportStrategy and NotificationChannel abstractions.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from app.application.observers import NotificationDispatcher
from app.application.ports import Clock, NotificationChannel
from app.domain.alert import Alert
from app.domain.alert_rules import AlertDecision, AlertRule
from app.domain.budget import BudgetUsage
from app.domain.enums import AlertLevel
from app.domain.money import Money, Period
from app.domain.reports import (
    ColumnKind,
    Report,
    ReportColumn,
    ReportDataSource,
    ReportMetric,
    ReportRegistry,
    ReportStrategy,
)
from tests.conftest import World, build_world
from tests.fakes import FixedClock

# --- Example 1: a new alert rule ---------------------------------------------


class ProjectedOverspendRule(AlertRule):
    """Warns early when the current pace of spending would exceed the limit by month-end."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    @property
    def key(self) -> str:
        return "projected-overspend"

    def evaluate(self, usage: BudgetUsage) -> AlertDecision | None:
        today = self._clock.today()
        if not usage.period.contains(today):
            return None
        projected = usage.spent.amount / today.day * usage.period.days
        if projected <= usage.limit.amount:
            return None
        return AlertDecision(
            level=AlertLevel.WARNING,
            message=(
                f"At this pace {usage.category_name} will reach "
                f"{Money(projected)} by month-end, over its {usage.limit} budget."
            ),
            threshold=Decimal(100),
        )


# --- Example 2: a new report -------------------------------------------------


class LargestExpensesReport(ReportStrategy):
    """The ten biggest expenses of the month."""

    key = "largest-expenses"
    title = "Largest expenses"
    description = "Your ten biggest expenses this month."

    def generate(self, period: Period, data: ReportDataSource) -> Report:
        expenses = [t for t in data.transactions_between(period.start, period.end) if t.is_expense]
        top = sorted(expenses, key=lambda t: t.amount, reverse=True)[:10]
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=(
                ReportColumn("date", "Date", ColumnKind.TEXT),
                ReportColumn("description", "Description", ColumnKind.TEXT),
                ReportColumn("amount", "Amount", ColumnKind.MONEY),
            ),
            rows=tuple(
                {
                    "date": t.occurred_on.isoformat(),
                    "description": t.description,
                    "amount": t.amount.amount,
                }
                for t in top
            ),
            metrics=(
                ReportMetric(
                    "Top 10 total",
                    sum((t.amount for t in top), Money.zero()).amount,
                    ColumnKind.MONEY,
                ),
            ),
        )


# --- Example 3: a new notification channel -----------------------------------


def _http_post(url: str, body: bytes) -> None:
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=10):
        pass


class WebhookChannel(NotificationChannel):
    """Posts alerts as JSON to a webhook (Slack, Teams, Discord, Zapier...)."""

    name = "webhook"

    def __init__(self, url: str, post: Callable[[str, bytes], None] = _http_post) -> None:
        self._url = url
        self._post = post

    def send(self, alert: Alert) -> None:
        self._post(self._url, json.dumps({"text": alert.message}).encode())


# --- Verification ------------------------------------------------------------


def test_projected_overspend_rule_warns_early() -> None:
    world = build_world(today=date(2026, 11, 10))
    rule = ProjectedOverspendRule(world.clock)
    food = world.category("Food", 3000)
    world.spend("1200", food)  # 40% used on day 10 of 30 → projects to 3600
    usage = world.budgets.statuses(Period(2026, 11))[0].usage
    decision = rule.evaluate(usage)
    assert decision is not None
    assert "3,600.00" in decision.message


def test_largest_expenses_report_plugs_in(world: World) -> None:
    from app.application.report_service import RepositoryReportDataSource

    food = world.category("Food")
    for amount in ("10", "500", "75"):
        world.spend(amount, food)
    registry = ReportRegistry().register(LargestExpensesReport())
    source = RepositoryReportDataSource(
        world.transactions_repo, world.categories_repo, world.budgets_repo
    )
    report = registry.get("largest-expenses").generate(Period(2026, 11), source)
    assert [row["amount"] for row in report.rows] == [
        Decimal("500.00"),
        Decimal("75.00"),
        Decimal("10.00"),
    ]


def test_webhook_channel_receives_alerts(world: World) -> None:
    posted: list[tuple[str, bytes]] = []
    world.monitor.attach(
        NotificationDispatcher(
            [WebhookChannel("https://hooks.example/x", lambda u, b: posted.append((u, b)))]
        )
    )
    world.spend("90", world.category("Food", 100))
    assert posted[0][0] == "https://hooks.example/x"
    assert b"Food has passed 80%" in posted[0][1]


def test_examples_need_no_changes_to_existing_classes() -> None:
    """The fixed clock is the only extra dependency, injected like any other."""
    assert ProjectedOverspendRule(FixedClock(date(2026, 1, 1))).key == "projected-overspend"
