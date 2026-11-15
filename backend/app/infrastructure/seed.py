"""Demo data so the app looks alive on first run.

Creates the demo personas from :mod:`app.infrastructure.demo_accounts`, each
with six months of activity scaled to their lifestyle, plus a few lightweight
sign-ups so the admin dashboard has a realistic user list. Everything goes
through the real services, so categorisation, recurring generation and
alerts behave exactly as they would for a person using the app.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from app.application.category_service import CategoryInput
from app.application.onboarding import StarterKit
from app.application.recurring_service import RecurringInput
from app.application.transaction_service import TransactionInput
from app.domain.enums import Frequency, TransactionType
from app.domain.money import Money, Period
from app.infrastructure.demo_accounts import DEMO_PERSONAS, Persona

if TYPE_CHECKING:
    from app.container import Container, UserScope

logger = logging.getLogger(__name__)

HISTORY_MONTHS = 5


@dataclass(frozen=True, slots=True)
class _CategorySeed:
    name: str
    color: str
    icon: str
    limit: int
    descriptions: tuple[str, ...]
    recurring_spend: int


_CATEGORIES = (
    _CategorySeed("Housing", "#5b6cf0", "house", 25000, (), 22000),
    _CategorySeed(
        "Food & Dining",
        "#e2a23b",
        "utensils",
        12000,
        (
            "Swiggy order",
            "Zomato dinner",
            "Starbucks coffee",
            "BigBasket groceries",
            "Sharma Dairy",
            "Restaurant lunch",
            "Dominos pizza",
        ),
        2800,
    ),
    _CategorySeed(
        "Transport",
        "#3b8fd9",
        "car",
        5000,
        ("Uber ride", "Ola auto", "Rapido bike taxi", "Petrol fill-up", "IRCTC ticket"),
        0,
    ),
    _CategorySeed("Subscriptions", "#9b6cf0", "repeat", 1500, ("YouTube Premium",), 768),
    _CategorySeed(
        "Shopping",
        "#df5f86",
        "shopping-bag",
        8000,
        ("AMZN Mktp order", "Flipkart order", "Myntra apparel", "IKEA home goods"),
        3200,
    ),
    _CategorySeed(
        "Entertainment",
        "#ea7a45",
        "clapperboard",
        3500,
        ("BookMyShow movie", "PVR cinemas", "Steam game"),
        0,
    ),
    _CategorySeed(
        "Utilities",
        "#2fa69a",
        "zap",
        4500,
        ("Electricity bill", "Jio recharge", "Water bill"),
        999,
    ),
    _CategorySeed(
        "Health",
        "#5fa564",
        "heart-pulse",
        3000,
        ("Apollo pharmacy", "PharmEasy order", "Dental check-up"),
        1500,
    ),
)

# Spend as a fraction of each budget this month: a mix of green, amber and red.
_CURRENT_MONTH_TARGETS = {
    "Food & Dining": Decimal("0.86"),
    "Entertainment": Decimal("1.08"),
    "Transport": Decimal("0.55"),
    "Shopping": Decimal("0.62"),
    "Utilities": Decimal("0.48"),
    "Health": Decimal("0.25"),
    "Subscriptions": Decimal("0.66"),
}

_EXTRA_USERS = (
    ("Ishaan Verma", 1),
    ("Ananya Iyer", 2),
    ("Kabir Singh", 3),
    ("Zoya Khan", 5),
    ("Vikram Rao", 6),
    ("Meera Pillai", 8),
    ("Arjun Das", 11),
    ("Sara Thomas", 13),
)
_EXTRA_DESCRIPTIONS = (
    "Swiggy order",
    "Uber ride",
    "AMZN Mktp order",
    "Netflix",
    "BigBasket groceries",
    "BookMyShow movie",
    "Electricity bill",
    "Apollo pharmacy",
    "Starbucks coffee",
    "Ola auto",
)


def _scaled(amount: int | Decimal, scale: Decimal, step: int = 1) -> Decimal:
    value = Decimal(amount) * scale / step
    return value.quantize(Decimal(1), ROUND_HALF_UP) * step


class DemoDataSeeder:
    """Populates one user's scope with six months of activity shaped by a persona."""

    def __init__(self, scope: UserScope, persona: Persona, today: date) -> None:
        self._scope = scope
        self._persona = persona
        self._scale = persona.scale
        self._today = today
        self._random = random.Random(persona.seed)

    def seed(self) -> None:
        """Create categories, rules, spending and recurring payments."""
        ids = self._seed_categories()
        StarterKit().apply(self._scope.categories, self._scope.rules)
        self._seed_variable_spending(ids)
        self._seed_recurring(ids)
        self._acknowledge_history()

    def _seed_categories(self) -> dict[str, str]:
        self._scope.categories.ensure_system_categories()
        ids: dict[str, str] = {}
        for seed in _CATEGORIES:
            limit = Money(_scaled(seed.limit, self._scale, step=500))
            details = self._scope.categories.create(
                CategoryInput(seed.name, seed.color, seed.icon, limit)
            )
            ids[seed.name] = details.category.id
        return ids

    def _seed_variable_spending(self, ids: dict[str, str]) -> None:
        current = Period.of(self._today)
        period = current
        for _ in range(HISTORY_MONTHS):
            period = period.previous()
        while period <= current:
            last_day = self._today.day if period == current else period.days
            for seed in _CATEGORIES:
                if not seed.descriptions:
                    continue
                limit = _scaled(seed.limit, self._scale, step=500)
                recurring = _scaled(seed.recurring_spend, self._scale)
                if period == current:
                    factor = _CURRENT_MONTH_TARGETS[seed.name]
                    recurring = recurring * Decimal(last_day) / period.days
                else:
                    factor = Decimal(self._random.randint(55, 92)) / 100
                self._spend(seed, ids[seed.name], period, last_day, limit * factor - recurring)
            if period != current and self._random.random() < 0.5:
                amount = _scaled(self._random.randint(8, 18) * 1000, self._scale)
                self._record(
                    TransactionType.INCOME,
                    amount,
                    "Freelance project payment",
                    period.start + timedelta(days=17),
                    None,
                )
            period = period.next()

    def _spend(
        self, seed: _CategorySeed, category_id: str, period: Period, last_day: int, target: Decimal
    ) -> None:
        if target <= 0:
            return
        count = max(1, min(int(target / (450 * self._scale)), 12))
        weights = [self._random.uniform(0.6, 1.4) for _ in range(count)]
        scale = target / Decimal(str(sum(weights)))
        for weight in weights:
            amount = (Decimal(str(weight)) * scale).quantize(Decimal(1))
            if amount <= 0:
                continue
            description = self._random.choice(seed.descriptions)
            day = period.start + timedelta(days=self._random.randint(0, last_day - 1))
            # "Sharma Dairy" is filed by hand, which teaches the user-defined handler.
            manual = category_id if description == "Sharma Dairy" else None
            self._record(TransactionType.EXPENSE, amount, description, day, manual)

    def _record(
        self,
        type: TransactionType,
        amount: Decimal,
        description: str,
        occurred_on: date,
        category_id: str | None,
    ) -> None:
        self._scope.transactions.record(
            TransactionInput(type, Money(amount), description, occurred_on, category_id)
        )

    def _seed_recurring(self, ids: dict[str, str]) -> None:
        first = Period.of(self._today)
        for _ in range(HISTORY_MONTHS):
            first = first.previous()
        previous = Period.of(self._today).previous()
        s = self._scale

        def money(amount: int) -> Money:
            return Money(_scaled(amount, s))

        payments = (
            RecurringInput(
                self._persona.income_label,
                money(95000),
                TransactionType.INCOME,
                Frequency.MONTHLY,
                first.start,
            ),
            RecurringInput(
                "Apartment rent",
                money(22000),
                TransactionType.EXPENSE,
                Frequency.MONTHLY,
                first.start,
                category_id=ids["Housing"],
            ),
            RecurringInput(
                "Netflix",
                Money.of(649),
                TransactionType.EXPENSE,
                Frequency.MONTHLY,
                first.start.replace(day=5),
            ),
            RecurringInput(
                "Spotify",
                Money.of(119),
                TransactionType.EXPENSE,
                Frequency.MONTHLY,
                first.start.replace(day=12),
            ),
            RecurringInput(
                "Gym membership",
                money(1500),
                TransactionType.EXPENSE,
                Frequency.MONTHLY,
                first.start.replace(day=3),
            ),
            RecurringInput(
                "Airtel broadband",
                Money.of(999),
                TransactionType.EXPENSE,
                Frequency.MONTHLY,
                first.start.replace(day=8),
            ),
            RecurringInput(
                "Laptop EMI",
                money(3200),
                TransactionType.EXPENSE,
                Frequency.MONTHLY,
                first.start.replace(day=15),
                category_id=ids["Shopping"],
            ),
            RecurringInput(
                "Weekly groceries",
                money(650),
                TransactionType.EXPENSE,
                Frequency.WEEKLY,
                first.start + timedelta(days=5),
            ),
            RecurringInput(
                "Newspaper delivery",
                Money.of(12),
                TransactionType.EXPENSE,
                Frequency.DAILY,
                previous.start,
                previous.end,
                category_id=ids["Utilities"],
            ),
        )
        for payment in payments:
            self._scope.recurring.create(payment)
        yoga = self._scope.recurring.create(
            RecurringInput(
                "Yoga class",
                money(300),
                TransactionType.EXPENSE,
                Frequency.WEEKLY,
                self._today - timedelta(days=10),
                category_id=ids["Health"],
            )
        )
        self._scope.recurring.pause(yoga.id)

    def _acknowledge_history(self) -> None:
        current = Period.of(self._today)
        for alert in self._scope.alerts.list_all(limit=200):
            if alert.period != current:
                self._scope.alerts.mark_read(alert.id)


def seed_demo_accounts(container: Container) -> bool:
    """Create the demo personas and extra sign-ups in an empty database."""
    if container.users.count() > 0:
        return False
    now = container.clock.now()
    today = container.clock.today()
    for persona in DEMO_PERSONAS:
        user = container.auth.create_account(
            name=persona.name,
            email=persona.email,
            password=persona.password,
            role=persona.role,
            created_at=now - timedelta(days=persona.joined_days_ago),
            onboard=False,
        )
        DemoDataSeeder(container.scope_for(user), persona, today).seed()
    _seed_extra_users(container, now, today)
    logger.info("Seeded %d demo accounts", len(DEMO_PERSONAS) + len(_EXTRA_USERS))
    return True


def _seed_extra_users(container: Container, now: datetime, today: date) -> None:
    rng = random.Random(2026)
    for index, (name, days_ago) in enumerate(_EXTRA_USERS):
        joined = datetime.combine(today - timedelta(days=days_ago), time(10), tzinfo=now.tzinfo)
        user = container.auth.create_account(
            name=name,
            email=f"{name.split()[0].lower()}@example.com",
            password="Demo@1234",
            created_at=joined,
        )
        scope = container.scope_for(user)
        for _ in range(rng.randint(4, 14)):
            day = today - timedelta(days=rng.randint(0, days_ago))
            scope.transactions.record(
                TransactionInput(
                    TransactionType.EXPENSE,
                    Money.of(rng.randint(80, 2400)),
                    rng.choice(_EXTRA_DESCRIPTIONS),
                    day,
                )
            )
        if index == len(_EXTRA_USERS) - 1:
            container.users.update(user.with_status(active=False))


__all__ = ["DemoDataSeeder", "seed_demo_accounts"]
