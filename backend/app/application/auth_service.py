"""Use cases: register, sign in, and authenticate a session token."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.ports import Clock, PasswordHasher, TokenIssuer, UserRepository
from app.domain.enums import UserRole
from app.domain.errors import AuthenticationError, ConflictError, TooManyAttemptsError
from app.domain.user import User, normalize_email, validate_password

OnboardingHook = Callable[[User], None]


@dataclass(frozen=True, slots=True)
class AuthResult:
    """A signed-in user and their session token."""

    user: User
    token: str


class LoginThrottle:
    """Slows down password guessing: N failures per e-mail within a window locks it briefly.

    In-memory and per process, which is enough for a single server; a
    multi-server deployment would back this with Redis behind the same API.
    """

    def __init__(
        self, clock: Clock, max_failures: int = 5, window: timedelta | None = None
    ) -> None:
        self._clock = clock
        self._max_failures = max_failures
        self._window = window or timedelta(minutes=5)
        self._failures: dict[str, list[datetime]] = {}
        self._lock = threading.Lock()

    def check(self, email: str) -> None:
        """Raise :class:`TooManyAttemptsError` if this e-mail is temporarily locked."""
        with self._lock:
            recent = self._recent(email)
        if len(recent) >= self._max_failures:
            raise TooManyAttemptsError(
                "Too many failed attempts. Wait a few minutes and try again."
            )

    def record_failure(self, email: str) -> None:
        """Remember a failed attempt."""
        with self._lock:
            self._failures[email] = [*self._recent(email), self._clock.now()]

    def reset(self, email: str) -> None:
        """Forget failures after a successful sign-in."""
        with self._lock:
            self._failures.pop(email, None)

    def _recent(self, email: str) -> list[datetime]:
        cutoff = self._clock.now() - self._window
        return [moment for moment in self._failures.get(email, []) if moment > cutoff]


class AuthService:
    """Accounts and sessions.

    Error messages never reveal whether an e-mail is registered, and a dummy
    hash is verified for unknown e-mails so response times don't leak it
    either.
    """

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenIssuer,
        clock: Clock,
        throttle: LoginThrottle,
        on_register: OnboardingHook,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock
        self._throttle = throttle
        self._on_register = on_register
        self._dummy_hash = hasher.hash("timing-equaliser-0")

    def create_account(
        self,
        *,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
        created_at: datetime | None = None,
        onboard: bool = True,
    ) -> User:
        """Create an account (used by sign-up and by the demo seeder)."""
        validate_password(password)
        if self._users.get_by_email(email) is not None:
            raise ConflictError("An account with this e-mail already exists")
        user = User.create(
            email=email,
            name=name,
            password_hash=self._hasher.hash(password),
            created_at=created_at or self._clock.now(),
            role=role,
        )
        self._users.add(user)
        if onboard:
            self._on_register(user)
        return user

    def register(self, *, name: str, email: str, password: str) -> AuthResult:
        """Sign up and sign in."""
        user = self.create_account(name=name, email=email, password=password)
        return self._session(user)

    def login(self, *, email: str, password: str) -> AuthResult:
        """Check credentials and start a session."""
        key = normalize_email(email)
        self._throttle.check(key)
        user = self._users.get_by_email(key)
        valid = self._hasher.verify(password, user.password_hash if user else self._dummy_hash)
        if user is None or not valid:
            self._throttle.record_failure(key)
            raise AuthenticationError("Incorrect e-mail or password")
        if not user.is_active:
            raise AuthenticationError(
                "This account has been deactivated. Contact an administrator."
            )
        self._throttle.reset(key)
        return self._session(user)

    def authenticate(self, token: str) -> User:
        """Resolve a session token to an active user."""
        claims = self._tokens.verify(token)
        if claims is None:
            raise AuthenticationError("Your session has expired. Sign in again.")
        user = self._users.get(claims.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Your session is no longer valid. Sign in again.")
        return user

    def _session(self, user: User) -> AuthResult:
        signed_in = user.signed_in(self._clock.now())
        self._users.update(signed_in)
        return AuthResult(user=signed_in, token=self._tokens.issue(signed_in))
