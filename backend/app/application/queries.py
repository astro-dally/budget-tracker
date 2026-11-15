"""Query objects and paging containers used by repositories and services."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.domain.enums import TransactionType
from app.domain.errors import DomainValidationError

MAX_PAGE_SIZE = 100


class SortField(StrEnum):
    """Columns transactions can be sorted by."""

    OCCURRED_ON = "occurred_on"
    AMOUNT = "amount"
    DESCRIPTION = "description"


class SortDirection(StrEnum):
    """Ascending or descending order."""

    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class TransactionQuery:
    """Filters, sorting and paging for listing transactions."""

    page: int = 1
    page_size: int = 20
    type: TransactionType | None = None
    category_id: str | None = None
    search: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    sort_by: SortField = SortField.OCCURRED_ON
    sort_direction: SortDirection = SortDirection.DESC

    def __post_init__(self) -> None:
        if self.page < 1:
            raise DomainValidationError("Page must be at least 1")
        if not 1 <= self.page_size <= MAX_PAGE_SIZE:
            raise DomainValidationError(f"Page size must be between 1 and {MAX_PAGE_SIZE}")
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise DomainValidationError("date_from must not be after date_to")

    @property
    def offset(self) -> int:
        """Number of rows to skip."""
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class Page[T]:
    """One page of results plus the total count."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        """Total number of pages (at least 1)."""
        return max(1, math.ceil(self.total / self.page_size))
