"""The ready-made demo logins, shown on the sign-in page when demo data is enabled."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import UserRole


@dataclass(frozen=True, slots=True)
class Persona:
    """A demo account and the shape of its spending."""

    name: str
    email: str
    password: str
    role: UserRole
    tagline: str
    income_label: str
    scale: Decimal
    seed: int
    joined_days_ago: int


DEMO_PERSONAS: tuple[Persona, ...] = (
    Persona(
        "Maya Kapoor",
        "admin@budgettracker.dev",
        "Admin@1234",
        UserRole.ADMIN,
        "Admin. Sees the whole platform and manages users.",
        "Salary — Northwind Labs",
        Decimal("1.25"),
        7,
        45,
    ),
    Persona(
        "Aarav Sharma",
        "aarav@demo.dev",
        "Demo@1234",
        UserRole.USER,
        "Young professional in Bengaluru, a few budgets running hot.",
        "Salary — Acme Corp",
        Decimal("1.00"),
        42,
        38,
    ),
    Persona(
        "Priya Nair",
        "priya@demo.dev",
        "Demo@1234",
        UserRole.USER,
        "Student on an internship stipend, small and tight budgets.",
        "Internship stipend",
        Decimal("0.40"),
        11,
        21,
    ),
    Persona(
        "Rohan Mehta",
        "rohan@demo.dev",
        "Demo@1234",
        UserRole.USER,
        "Family of four with bigger bills and an EMI.",
        "Salary — Mehta & Sons",
        Decimal("1.90"),
        99,
        9,
    ),
)
