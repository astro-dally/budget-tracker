"""Security adapters: scrypt password hashing and JWT session tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.application.ports import Clock, TokenClaims
from app.domain.enums import UserRole
from app.domain.user import User


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


class ScryptPasswordHasher:
    """Hashes passwords with scrypt from the standard library.

    scrypt is memory-hard (recommended by OWASP), so brute-forcing a leaked
    hash on GPUs is expensive. Each hash has its own random salt and stores
    its parameters, so they can be raised later without breaking old hashes.
    """

    def __init__(self, n: int = 2**14, r: int = 8, p: int = 1) -> None:
        self._n, self._r, self._p = n, r, p

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=self._n, r=self._r, p=self._p)
        return f"scrypt${self._n}${self._r}${self._p}${_b64(salt)}${_b64(digest)}"

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            scheme, n, r, p, salt, expected = password_hash.split("$")
            if scheme != "scrypt":
                return False
            digest = hashlib.scrypt(
                password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p)
            )
        except ValueError:
            return False
        return hmac.compare_digest(digest, base64.b64decode(expected))


class JwtTokenIssuer:
    """Signs stateless session tokens (HS256) carrying the user id and role."""

    algorithm = "HS256"

    def __init__(self, secret: str, clock: Clock, lifetime: timedelta) -> None:
        self._secret = secret
        self._clock = clock
        self._lifetime = lifetime

    def issue(self, user: User) -> str:
        now = self._clock.now()
        payload = {
            "sub": user.id,
            "role": user.role.value,
            "iat": int(now.timestamp()),
            "exp": int((now + self._lifetime).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self.algorithm)

    def verify(self, token: str) -> TokenClaims | None:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self.algorithm],
                options={"require": ["sub", "exp"], "verify_exp": False},
            )
            expires_at = datetime.fromtimestamp(int(payload["exp"]), UTC)
            if expires_at <= self._clock.now():
                return None
            return TokenClaims(
                user_id=str(payload["sub"]),
                role=UserRole(payload.get("role", UserRole.USER.value)),
                expires_at=expires_at,
            )
        except (jwt.PyJWTError, ValueError, KeyError):
            return None
