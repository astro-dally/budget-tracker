"""Enumerations used across the domain."""

from enum import StrEnum


class TransactionType(StrEnum):
    """Whether money came in or went out."""

    INCOME = "income"
    EXPENSE = "expense"


class CategorySource(StrEnum):
    """How a transaction got its category.

    ``MANUAL`` choices feed the user-defined categorisation handler; ``AUTO``
    ones are excluded so the system never learns from its own guesses.
    """

    MANUAL = "manual"
    AUTO = "auto"


class Frequency(StrEnum):
    """How often a recurring payment repeats."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AlertLevel(StrEnum):
    """Severity of a budget alert."""

    WARNING = "warning"
    CRITICAL = "critical"


class BudgetHealth(StrEnum):
    """Traffic-light status of a budget, used by progress bars."""

    OK = "ok"
    WARNING = "warning"
    EXCEEDED = "exceeded"


class UserRole(StrEnum):
    """What a signed-in person may do."""

    USER = "user"
    ADMIN = "admin"
