"""The :class:`CategoryRule` entity: a user-managed keyword → category mapping."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.errors import DomainValidationError
from app.domain.ids import new_id


@dataclass(frozen=True, slots=True)
class CategoryRule:
    """Maps a keyword (e.g. ``uber``) to a category (e.g. *Transport*).

    Matching is case-insensitive and respects word boundaries, so the rule
    ``ola`` matches "Ola ride" but not "Coca-Cola".
    """

    id: str
    keyword: str
    category_id: str

    def __post_init__(self) -> None:
        keyword = " ".join(self.keyword.split()).lower()
        if not 2 <= len(keyword) <= 50:
            raise DomainValidationError("Keyword must be between 2 and 50 characters")
        object.__setattr__(self, "keyword", keyword)

    @classmethod
    def create(cls, keyword: str, category_id: str) -> CategoryRule:
        """Factory method that assigns a fresh id."""
        return cls(id=new_id(), keyword=keyword, category_id=category_id)

    def matches(self, description: str) -> bool:
        """Return True when the keyword appears in ``description`` as a whole word."""
        return contains_term(description, self.keyword)


def contains_term(text: str, term: str) -> bool:
    """Case-insensitive whole-word containment shared by keyword and merchant matching."""
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None
