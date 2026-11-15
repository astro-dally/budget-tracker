"""The :class:`Transaction` entity (Single Responsibility: one money movement)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from app.domain.enums import CategorySource, TransactionType
from app.domain.errors import DomainValidationError
from app.domain.ids import new_id
from app.domain.money import Money, Period

MAX_DESCRIPTION_LENGTH = 200


def normalize_description(text: str) -> str:
    """Canonical form used for matching descriptions: trimmed and lower-cased."""
    return " ".join(text.split()).lower()


@dataclass(frozen=True, slots=True)
class Transaction:
    """A single income or expense.

    The entity only guards its own invariants (positive amount, non-empty
    description). It does not categorise itself, check budgets or persist
    itself; those are separate responsibilities (SRP).
    """

    id: str
    type: TransactionType
    amount: Money
    description: str
    occurred_on: date
    category_id: str | None = None
    category_source: CategorySource = CategorySource.MANUAL
    recurring_id: str | None = None

    def __post_init__(self) -> None:
        if not self.amount.is_positive():
            raise DomainValidationError("Transaction amount must be greater than zero")
        cleaned = " ".join(self.description.split())
        if not cleaned:
            raise DomainValidationError("Description must not be empty")
        if len(cleaned) > MAX_DESCRIPTION_LENGTH:
            raise DomainValidationError(
                f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters"
            )
        object.__setattr__(self, "description", cleaned)

    @classmethod
    def create(
        cls,
        *,
        type: TransactionType,
        amount: Money,
        description: str,
        occurred_on: date,
        category_id: str | None,
        category_source: CategorySource,
        recurring_id: str | None = None,
    ) -> Transaction:
        """Factory method that assigns a fresh id."""
        return cls(
            id=new_id(),
            type=type,
            amount=amount,
            description=description,
            occurred_on=occurred_on,
            category_id=category_id,
            category_source=category_source,
            recurring_id=recurring_id,
        )

    @property
    def is_expense(self) -> bool:
        """True for money going out."""
        return self.type is TransactionType.EXPENSE

    @property
    def period(self) -> Period:
        """The month this transaction belongs to."""
        return Period.of(self.occurred_on)

    def recategorized(self, category_id: str, source: CategorySource) -> Transaction:
        """Return a copy assigned to another category."""
        return replace(self, category_id=category_id, category_source=source)
