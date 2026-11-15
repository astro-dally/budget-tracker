"""Value objects: :class:`Money` and :class:`Period`.

Both are immutable ``frozen`` dataclasses with ``slots``. Value objects are
compared by value, can be shared freely, and validate themselves on
construction, so an invalid amount or month can never exist in the system.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.domain.errors import DomainValidationError

_CENT = Decimal("0.01")
_MAX_AMOUNT = Decimal("9999999999.99")


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """An exact monetary amount in the application's single currency.

    Uses :class:`decimal.Decimal`, never ``float``, because binary floating
    point cannot represent values such as 0.10 exactly. Amounts are rounded
    half-up to two decimal places on construction.
    """

    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise DomainValidationError("Money amount must be a Decimal")
        if not self.amount.is_finite():
            raise DomainValidationError("Money amount must be finite")
        quantized = self.amount.quantize(_CENT, rounding=ROUND_HALF_UP)
        if abs(quantized) > _MAX_AMOUNT:
            raise DomainValidationError("Money amount is too large")
        object.__setattr__(self, "amount", quantized)

    @classmethod
    def of(cls, value: str | int | Decimal) -> Money:
        """Build Money from a string, int or Decimal (floats are rejected)."""
        if isinstance(value, float):
            raise DomainValidationError("Use Decimal or str for money, never float")
        try:
            return cls(Decimal(value))
        except (InvalidOperation, TypeError) as exc:
            raise DomainValidationError(f"'{value}' is not a valid amount") from exc

    @classmethod
    def zero(cls) -> Money:
        """Return an amount of zero."""
        return cls(Decimal(0))

    @classmethod
    def from_minor_units(cls, minor: int) -> Money:
        """Build Money from an integer number of cents (used by persistence)."""
        return cls(Decimal(minor) / 100)

    def to_minor_units(self) -> int:
        """Return the amount as an integer number of cents."""
        return int(self.amount * 100)

    def is_positive(self) -> bool:
        """Return True when the amount is strictly greater than zero."""
        return self.amount > 0

    def percent_of(self, whole: Money) -> Decimal:
        """Return this amount as a percentage of ``whole``, rounded to one decimal place."""
        if not whole.is_positive():
            raise DomainValidationError("Cannot compute a percentage of a non-positive amount")
        return (self.amount * 100 / whole.amount).quantize(Decimal("0.1"), ROUND_HALF_UP)

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        return Money(self.amount - other.amount)

    def __str__(self) -> str:
        return f"{self.amount:,.2f}"


@dataclass(frozen=True, slots=True, order=True)
class Period:
    """A calendar month, the unit for budgets, alerts and reports."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise DomainValidationError("Month must be between 1 and 12")
        if not 1900 <= self.year <= 9999:
            raise DomainValidationError("Year is out of range")

    @classmethod
    def of(cls, day: date) -> Period:
        """Return the period containing ``day``."""
        return cls(day.year, day.month)

    @classmethod
    def parse(cls, text: str) -> Period:
        """Parse ``YYYY-MM`` into a Period."""
        try:
            year_text, month_text = text.split("-")
            return cls(int(year_text), int(month_text))
        except ValueError as exc:
            raise DomainValidationError(
                f"'{text}' is not a valid month (expected YYYY-MM)"
            ) from exc

    @property
    def start(self) -> date:
        """First day of the month."""
        return date(self.year, self.month, 1)

    @property
    def end(self) -> date:
        """Last day of the month."""
        return date(self.year, self.month, calendar.monthrange(self.year, self.month)[1])

    @property
    def days(self) -> int:
        """Number of days in the month."""
        return self.end.day

    def contains(self, day: date) -> bool:
        """Return True when ``day`` falls inside this month."""
        return self.start <= day <= self.end

    def next(self) -> Period:
        """Return the following month."""
        return Period(self.year + 1, 1) if self.month == 12 else Period(self.year, self.month + 1)

    def previous(self) -> Period:
        """Return the preceding month."""
        return Period(self.year - 1, 12) if self.month == 1 else Period(self.year, self.month - 1)

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"
