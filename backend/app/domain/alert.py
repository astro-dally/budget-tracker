"""The :class:`Alert` entity: a record that a budget threshold was crossed."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from app.domain.enums import AlertLevel
from app.domain.ids import new_id
from app.domain.money import Money, Period


@dataclass(frozen=True, slots=True)
class Alert:
    """An alert raised when an :class:`~app.domain.alert_rules.AlertRule` fires.

    ``(category_id, period, rule_key)`` identifies an alert uniquely; the
    persistence layer enforces that with a unique constraint, which is what
    makes "fire once per category per month" hold even under concurrency.
    The category name is copied in so history stays readable if the
    category is later renamed or deleted.
    """

    id: str
    category_id: str
    category_name: str
    period: Period
    rule_key: str
    level: AlertLevel
    threshold: Decimal
    message: str
    spent: Money
    limit: Money
    created_at: datetime
    is_read: bool = False

    @classmethod
    def create(
        cls,
        *,
        category_id: str,
        category_name: str,
        period: Period,
        rule_key: str,
        level: AlertLevel,
        threshold: Decimal,
        message: str,
        spent: Money,
        limit: Money,
        created_at: datetime,
    ) -> Alert:
        """Factory method that assigns a fresh id."""
        return cls(
            id=new_id(),
            category_id=category_id,
            category_name=category_name,
            period=period,
            rule_key=rule_key,
            level=level,
            threshold=threshold,
            message=message,
            spent=spent,
            limit=limit,
            created_at=created_at,
        )

    def mark_read(self) -> Alert:
        """Return a copy flagged as read."""
        return replace(self, is_read=True)
