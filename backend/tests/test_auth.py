"""Accounts: registration, sign-in, throttling, sessions and security adapters."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.application.auth_service import AuthService, LoginThrottle
from app.domain.enums import UserRole
from app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainValidationError,
    TooManyAttemptsError,
)
from app.domain.user import User, validate_password
from app.infrastructure.security import JwtTokenIssuer, ScryptPasswordHasher
from tests.fakes import FastHasher, FixedClock, InMemoryUserRepository


class Harness:
    def __init__(self) -> None:
        self.clock = FixedClock(date(2026, 11, 14))
        self.users = InMemoryUserRepository()
        self.onboarded: list[str] = []
        self.tokens = JwtTokenIssuer(
            "test-secret-0123456789abcdef0123", self.clock, timedelta(hours=1)
        )
        self.auth = AuthService(
            self.users,
            FastHasher(),
            self.tokens,
            self.clock,
            LoginThrottle(self.clock, max_failures=3),
            on_register=lambda user: self.onboarded.append(user.email),
        )


@pytest.fixture
def h() -> Harness:
    return Harness()


def test_register_creates_onboarded_account_and_session(h: Harness) -> None:
    result = h.auth.register(name="Asha", email=" Asha@Example.COM ", password="secret123")
    assert result.user.email == "asha@example.com"
    assert result.user.role is UserRole.USER
    assert result.user.last_login_at is not None
    assert h.onboarded == ["asha@example.com"]
    assert h.auth.authenticate(result.token).id == result.user.id


def test_email_must_be_unique_case_insensitively(h: Harness) -> None:
    h.auth.register(name="A", email="a@x.dev", password="secret123")
    with pytest.raises(ConflictError):
        h.auth.register(name="B", email="A@X.DEV", password="secret123")


@pytest.mark.parametrize("password", ["short1", "allletters", "12345678", "x" * 129 + "1"])
def test_password_policy(password: str) -> None:
    with pytest.raises(DomainValidationError):
        validate_password(password)


def test_login_never_reveals_which_part_was_wrong(h: Harness) -> None:
    h.auth.register(name="A", email="a@x.dev", password="secret123")
    with pytest.raises(AuthenticationError) as wrong_password:
        h.auth.login(email="a@x.dev", password="nope12345")
    with pytest.raises(AuthenticationError) as unknown_email:
        h.auth.login(email="ghost@x.dev", password="secret123")
    assert str(wrong_password.value) == str(unknown_email.value)


def test_repeated_failures_are_throttled_then_expire(h: Harness) -> None:
    h.auth.register(name="A", email="a@x.dev", password="secret123")
    for _ in range(3):
        with pytest.raises(AuthenticationError):
            h.auth.login(email="a@x.dev", password="wrong1234")
    with pytest.raises(TooManyAttemptsError):
        h.auth.login(email="a@x.dev", password="secret123")
    h.clock.advance(1)
    assert h.auth.login(email="a@x.dev", password="secret123").user.email == "a@x.dev"


def test_deactivated_accounts_cannot_sign_in_or_use_old_tokens(h: Harness) -> None:
    token = h.auth.register(name="A", email="a@x.dev", password="secret123").token
    user = h.users.get_by_email("a@x.dev")
    assert user is not None
    h.users.update(user.with_status(active=False))
    with pytest.raises(AuthenticationError, match="deactivated"):
        h.auth.login(email="a@x.dev", password="secret123")
    with pytest.raises(AuthenticationError):
        h.auth.authenticate(token)


def test_tokens_expire_and_reject_tampering(h: Harness) -> None:
    token = h.auth.register(name="A", email="a@x.dev", password="secret123").token
    with pytest.raises(AuthenticationError):
        h.auth.authenticate(token[:-2] + ("AA" if not token.endswith("AA") else "BB"))
    h.clock.advance(1)
    with pytest.raises(AuthenticationError):
        h.auth.authenticate(token)


def test_tokens_signed_with_another_secret_are_rejected(h: Harness) -> None:
    user = h.auth.register(name="A", email="a@x.dev", password="secret123").user
    forged = JwtTokenIssuer("attacker-secret-0123456789abcdef", h.clock, timedelta(hours=1))
    with pytest.raises(AuthenticationError):
        h.auth.authenticate(forged.issue(user))


def test_scrypt_hasher_salts_and_verifies() -> None:
    hasher = ScryptPasswordHasher(n=2**10)
    first, second = hasher.hash("secret123"), hasher.hash("secret123")
    assert first != second
    assert hasher.verify("secret123", first)
    assert not hasher.verify("secret124", first)
    assert not hasher.verify("secret123", "garbage")
    assert not hasher.verify("secret123", "bcrypt$1$2$3$4$5")


def test_user_entity_validates_and_normalises() -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    user = User.create(email="  Me@Site.IO", name="  Me  ", password_hash="h", created_at=created)
    assert (user.email, user.name) == ("me@site.io", "Me")
    assert user.with_role(UserRole.ADMIN).is_admin
    with pytest.raises(DomainValidationError):
        User.create(email="not-an-email", name="Me", password_hash="h", created_at=created)
