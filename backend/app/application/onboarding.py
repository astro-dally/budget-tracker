"""Starter kit applied to every new account so the app is useful from minute one."""

from __future__ import annotations

from app.application.category_service import CategoryInput, CategoryService
from app.application.rule_service import RuleService

STARTER_CATEGORIES: tuple[tuple[str, str, str], ...] = (
    ("Housing", "#5b6cf0", "house"),
    ("Food & Dining", "#e2a23b", "utensils"),
    ("Transport", "#3b8fd9", "car"),
    ("Subscriptions", "#9b6cf0", "repeat"),
    ("Shopping", "#df5f86", "shopping-bag"),
    ("Entertainment", "#ea7a45", "clapperboard"),
    ("Utilities", "#2fa69a", "zap"),
    ("Health", "#5fa564", "heart-pulse"),
)

STARTER_RULES: dict[str, str] = {
    "uber": "Transport",
    "uber eats": "Food & Dining",
    "ola": "Transport",
    "rapido": "Transport",
    "petrol": "Transport",
    "netflix": "Subscriptions",
    "spotify": "Subscriptions",
    "rent": "Housing",
    "electricity": "Utilities",
    "water bill": "Utilities",
    "broadband": "Utilities",
    "groceries": "Food & Dining",
    "restaurant": "Food & Dining",
    "pharmacy": "Health",
    "gym": "Health",
    "dental": "Health",
    "movie": "Entertainment",
}


class StarterKit:
    """Creates common categories (without limits) and keyword rules for a new user."""

    def apply(self, categories: CategoryService, rules: RuleService) -> dict[str, str]:
        """Create anything missing and return a name → category id map."""
        categories.ensure_system_categories()
        existing = {d.category.name: d.category.id for d in categories.list_all()}
        for name, color, icon in STARTER_CATEGORIES:
            if name not in existing:
                existing[name] = categories.create(CategoryInput(name, color, icon)).category.id
        known = {rule.keyword for rule in rules.list_all()}
        for keyword, category in STARTER_RULES.items():
            if keyword not in known and category in existing:
                rules.create(keyword, existing[category])
        return existing
