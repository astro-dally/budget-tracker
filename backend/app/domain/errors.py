"""Domain exceptions.

The API layer translates these into HTTP status codes, so the domain never
needs to know about HTTP (Dependency Inversion: the outer layer adapts to
the inner one).
"""


class DomainError(Exception):
    """Base class for every error raised by the domain or application layers."""


class DomainValidationError(DomainError):
    """A value broke a business invariant (e.g. a negative budget limit)."""


class NotFoundError(DomainError):
    """A requested entity does not exist."""

    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} '{entity_id}' was not found")
        self.entity = entity
        self.entity_id = entity_id


class ConflictError(DomainError):
    """The operation conflicts with existing state (duplicate name, system category...)."""


class DuplicateRecurrenceError(ConflictError):
    """A recurring payment was already materialised for that date (idempotency guard)."""


class AuthenticationError(DomainError):
    """Credentials or a session token were missing, wrong or expired (HTTP 401)."""


class PermissionDeniedError(DomainError):
    """The signed-in user may not perform this action (HTTP 403)."""


class TooManyAttemptsError(DomainError):
    """Too many failed sign-in attempts in a short window (HTTP 429)."""
