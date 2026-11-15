"""Strategy + registry: reports."""

from datetime import date
from decimal import Decimal

import pytest

from app.application.transaction_service import TransactionInput
from app.container import build_report_registry
from app.domain.enums import TransactionType
from app.domain.errors import ConflictError, NotFoundError
from app.domain.money import Money, Period
from app.domain.reports import (
    ColumnKind,
    MonthlySummaryReport,
    Report,
    ReportColumn,
    ReportDataSource,
    ReportMetric,
    ReportRegistry,
    ReportStrategy,
)
from tests.conftest import World

NOV = Period(2026, 11)


def _seed(world: World) -> None:
    food = world.category("Food", 1000)
    fun = world.category("Fun", 200)
    world.transactions.record(
        TransactionInput(TransactionType.INCOME, Money.of(5000), "Salary", date(2026, 11, 1))
    )
    world.spend("600", food, on=date(2026, 11, 3))
    world.spend("400", food, on=date(2026, 11, 20))
    world.spend("250", fun, on=date(2026, 11, 29))
    world.spend("100", food, on=date(2026, 10, 12))


def test_registry_lists_strategies_in_order() -> None:
    keys = [s.key for s in build_report_registry().available()]
    assert keys == ["monthly-summary", "category-wise", "spending-trend"]


def test_registry_rejects_unknown_and_duplicate_keys() -> None:
    registry = build_report_registry()
    with pytest.raises(NotFoundError):
        registry.get("nope")
    with pytest.raises(ConflictError):
        registry.register(MonthlySummaryReport())


def test_monthly_summary(world: World) -> None:
    _seed(world)
    report = world.reports.generate("monthly-summary", NOV)
    metrics = {m.label: m.value for m in report.metrics}
    assert metrics["Income"] == Decimal("5000.00")
    assert metrics["Expenses"] == Decimal("1250.00")
    assert metrics["Net savings"] == Decimal("3750.00")
    assert metrics["Savings rate"] == Decimal("75.0")
    assert metrics["Largest expense"] == Decimal("600.00")
    assert len(report.rows) == 5
    assert report.rows[0]["expenses"] == Decimal("600.00")


def test_category_wise(world: World) -> None:
    _seed(world)
    report = world.reports.generate("category-wise", NOV)
    assert [r["category"] for r in report.rows] == ["Food", "Fun"]
    assert report.rows[0]["used"] == Decimal("100.0")
    metrics = {m.label: m.value for m in report.metrics}
    assert metrics["Categories over budget"] == 2
    assert metrics["Top category"] == "Food"


def test_spending_trend(world: World) -> None:
    _seed(world)
    report = world.reports.generate("spending-trend", NOV)
    assert len(report.rows) == 6
    assert report.rows[-1]["month"] == "Nov 2026"
    change = {m.label: m.value for m in report.metrics}["Spend change vs last month"]
    assert change == Decimal("1150.0")


class TransactionCountReport(ReportStrategy):
    """A new report added without editing any existing class (Open/Closed)."""

    key = "transaction-count"
    title = "Transaction count"
    description = "How many transactions were recorded."

    def generate(self, period: Period, data: ReportDataSource) -> Report:
        count = len(data.transactions_between(period.start, period.end))
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=(ReportColumn("count", "Count", ColumnKind.NUMBER),),
            rows=({"count": count},),
            metrics=(ReportMetric("Transactions", count, ColumnKind.NUMBER),),
        )


def test_new_report_plugs_into_the_registry(world: World) -> None:
    _seed(world)
    registry = ReportRegistry().register(TransactionCountReport())
    report = registry.get("transaction-count").generate(NOV, _source(world))
    assert report.rows[0]["count"] == 4


def _source(world: World) -> ReportDataSource:
    from app.application.report_service import RepositoryReportDataSource

    return RepositoryReportDataSource(
        world.transactions_repo, world.categories_repo, world.budgets_repo
    )
