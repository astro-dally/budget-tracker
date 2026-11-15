"""The :class:`User` entity: a person who owns budgets and transactions."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime

from app.domain.enums import UserRole
from app.domain.errors import DomainValidationError
from app.domain.ids import new_id

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def normalize_email(email: str) -> str:
    """Canonical e-mail form used for uniqueness and look-ups."""
    return email.strip().lower()


def validate_password(password: str) -> None:
    """Enforce a minimal password policy: 8-128 characters with a letter and a digit."""
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise DomainValidationError(
            f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters long"
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise DomainValidationError("Password must contain at least one letter and one number")


@dataclass(frozen=True, slots=True)
class User:
    """An account. Holds identity and role only; it never sees a plain-text password.

    Password hashing and token signing are infrastructure concerns behind
    the ``PasswordHasher`` and ``TokenIssuer`` ports, so this entity stays
    free of cryptography libraries.
    """

    id: str
    email: str
    name: str
    password_hash: str
    created_at: datetime
    role: UserRole = UserRole.USER
    is_active: bool = True
    last_login_at: datetime | None = None

    def __post_init__(self) -> None:
        email = normalize_email(self.email)
        if not _EMAIL.match(email) or len(email) > 254:
            raise DomainValidationError("Enter a valid e-mail address")
        name = " ".join(self.name.split())
        if not 1 <= len(name) <= 60:
            raise DomainValidationError("Name must be between 1 and 60 characters")
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "name", name)

    @classmethod
    def create(
        cls,
        *,
        email: str,
        name: str,
        password_hash: str,
        created_at: datetime,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Factory method that assigns a fresh id."""
        return cls(
            id=new_id(),
            email=email,
            name=name,
            password_hash=password_hash,
            created_at=created_at,
            role=role,
        )

    @property
    def is_admin(self) -> bool:
        """True for administrators."""
        return self.role is UserRole.ADMIN

    def signed_in(self, at: datetime) -> User:
        """Return a copy with the last sign-in time updated."""
        return replace(self, last_login_at=at)

    def with_status(self, *, active: bool) -> User:
        """Return an activated or deactivated copy."""
        return replace(self, is_active=active)

    def with_role(self, role: UserRole) -> User:
        """Return a copy with another role."""
        return replace(self, role=role)
