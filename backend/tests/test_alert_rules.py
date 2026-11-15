"""Strategy: alert rules are interchangeable and exact."""

from decimal import Decimal

import pytest

from app.domain.alert_rules import AlertDecision, AlertRule, PercentageThresholdRule
from app.domain.budget import Budget, BudgetUsage
from app.domain.enums import AlertLevel
from app.domain.errors import DomainValidationError
from app.domain.money import Money, Period


def usage(spent: str, limit: str = "1000") -> BudgetUsage:
    return Budget("c1", Money.of(limit)).usage(
        category_name="Food", period=Period(2026, 11), spent=Money.of(spent)
    )


def test_80_percent_rule_is_exact_at_the_boundary() -> None:
    rule = PercentageThresholdRule(80)
    assert rule.evaluate(usage("799.99")) is None
    decision = rule.evaluate(usage("800.00"))
    assert decision is not None
    assert decision.level is AlertLevel.WARNING
    assert "80.0%" in decision.message


def test_100_percent_rule_is_critical() -> None:
    decision = PercentageThresholdRule(100).evaluate(usage("1200"))
    assert decision is not None
    assert decision.level is AlertLevel.CRITICAL
    assert "over budget" in decision.message


def test_keys_are_stable_and_distinct() -> None:
    assert PercentageThresholdRule(80).key == "percent-80"
    assert PercentageThresholdRule(Decimal("90.5")).key == "percent-90.5"


def test_level_can_be_overridden() -> None:
    decision = PercentageThresholdRule(50, AlertLevel.CRITICAL).evaluate(usage("600"))
    assert decision is not None
    assert decision.level is AlertLevel.CRITICAL


@pytest.mark.parametrize("percent", [0, -10])
def test_rejects_non_positive_thresholds(percent: int) -> None:
    with pytest.raises(DomainValidationError):
        PercentageThresholdRule(percent)


class RemainingAmountRule(AlertRule):
    """A brand-new strategy written without modifying any existing class."""

    def __init__(self, minimum: str) -> None:
        self._minimum = Money.of(minimum)

    @property
    def key(self) -> str:
        return f"remaining-{self._minimum.amount}"

    def evaluate(self, usage: BudgetUsage) -> AlertDecision | None:
        if usage.remaining >= self._minimum:
            return None
        return AlertDecision(AlertLevel.WARNING, "Running low", Decimal(0))


def test_new_rule_is_substitutable() -> None:
    rules: list[AlertRule] = [PercentageThresholdRule(80), RemainingAmountRule("300")]
    fired = [rule.key for rule in rules if rule.evaluate(usage("750"))]
    assert fired == ["remaining-300.00"]
