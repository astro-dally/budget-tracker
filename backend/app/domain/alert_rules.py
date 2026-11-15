"""Strategy pattern: alert rules.

``AlertRule`` is the *Strategy* interface; ``PercentageThresholdRule`` is a
*Concrete Strategy*. ``BudgetMonitor`` (the *Context*) holds a list of rules
and asks each one to evaluate a :class:`BudgetUsage`. A new kind of rule is a
new subclass registered in the composition root; no existing class changes
(Open/Closed). Every rule honours the same contract (return a decision or
None, never mutate the usage), so rules are interchangeable (Liskov).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.domain.budget import EXCEEDED_PERCENT, BudgetUsage
from app.domain.enums import AlertLevel
from app.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class AlertDecision:
    """What a rule decided: the severity, message and threshold that was crossed."""

    level: AlertLevel
    message: str
    threshold: Decimal


class AlertRule(ABC):
    """Strategy interface: decides whether a budget usage deserves an alert."""

    @property
    @abstractmethod
    def key(self) -> str:
        """Stable identifier used to de-duplicate alerts (e.g. ``percent-80``)."""

    @abstractmethod
    def evaluate(self, usage: BudgetUsage) -> AlertDecision | None:
        """Return a decision when the rule fires for ``usage``, otherwise None."""


class PercentageThresholdRule(AlertRule):
    """Concrete strategy: fires when spending reaches ``percent`` of the limit.

    ``PercentageThresholdRule(80)`` warns; ``PercentageThresholdRule(100)`` is
    critical. The level defaults from the percentage but can be overridden.
    """

    def __init__(self, percent: int | Decimal, level: AlertLevel | None = None) -> None:
        self._percent = Decimal(percent)
        if self._percent <= 0:
            raise DomainValidationError("Threshold percentage must be greater than zero")
        self._level = level or (
            AlertLevel.CRITICAL if self._percent >= EXCEEDED_PERCENT else AlertLevel.WARNING
        )

    @property
    def percent(self) -> Decimal:
        """The configured threshold percentage."""
        return self._percent

    @property
    def key(self) -> str:
        return f"percent-{self._percent.normalize():f}"

    def evaluate(self, usage: BudgetUsage) -> AlertDecision | None:
        if not usage.has_reached(self._percent):
            return None
        if self._percent >= EXCEEDED_PERCENT:
            message = (
                f"{usage.category_name} is over budget: spent {usage.spent} "
                f"of {usage.limit} for {usage.period}."
            )
        else:
            message = (
                f"{usage.category_name} has passed {self._percent.normalize():f}% of its budget: "
                f"{usage.spent} of {usage.limit} spent ({usage.percent_used}%) in {usage.period}."
            )
        return AlertDecision(level=self._level, message=message, threshold=self._percent)

    def __repr__(self) -> str:
        return f"PercentageThresholdRule({self._percent})"
