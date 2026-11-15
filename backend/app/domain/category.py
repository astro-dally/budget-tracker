"""The :class:`Category` entity (Single Responsibility: naming and grouping spend)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.errors import DomainValidationError
from app.domain.ids import new_id

UNCATEGORIZED_NAME = "Uncategorized"
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_MAX_NAME_LENGTH = 50


@dataclass(frozen=True, slots=True)
class Category:
    """A named bucket of spending such as *Transport* or *Subscriptions*.

    A category does not hold its spending limit; that belongs to
    :class:`~app.domain.budget.Budget`, so naming/appearance and money rules
    can change independently (SRP).
    """

    id: str
    name: str
    color: str = "#64748b"
    icon: str = "tag"
    is_system: bool = False

    def __post_init__(self) -> None:
        name = " ".join(self.name.split())
        if not name:
            raise DomainValidationError("Category name must not be empty")
        if len(name) > _MAX_NAME_LENGTH:
            raise DomainValidationError(
                f"Category name must be at most {_MAX_NAME_LENGTH} characters"
            )
        if not _HEX_COLOR.match(self.color):
            raise DomainValidationError("Color must be a hex value such as #22c55e")
        object.__setattr__(self, "name", name)

    @classmethod
    def create(cls, name: str, color: str, icon: str, *, is_system: bool = False) -> Category:
        """Factory method that assigns a fresh id."""
        return cls(id=new_id(), name=name, color=color, icon=icon, is_system=is_system)
