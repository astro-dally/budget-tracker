"""Use cases: manage categories (and their optional budget limit)."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.budget_service import BudgetService
from app.application.ports import (
    CategoryRepository,
    CategoryRuleRepository,
    RecurringPaymentRepository,
    TransactionRepository,
)
from app.domain.budget import Budget
from app.domain.category import UNCATEGORIZED_NAME, Category
from app.domain.errors import ConflictError, NotFoundError
from app.domain.money import Money


@dataclass(frozen=True, slots=True)
class CategoryInput:
    """Data for creating or updating a category."""

    name: str
    color: str
    icon: str
    monthly_limit: Money | None = None


@dataclass(frozen=True, slots=True)
class CategoryDetails:
    """A category with its budget (if any)."""

    category: Category
    budget: Budget | None


class CategoryService:
    """Creates, edits and deletes categories; delegates limits to :class:`BudgetService`."""

    def __init__(
        self,
        categories: CategoryRepository,
        budgets: BudgetService,
        rules: CategoryRuleRepository,
        transactions: TransactionRepository,
        recurring: RecurringPaymentRepository,
    ) -> None:
        self._categories = categories
        self._budgets = budgets
        self._rules = rules
        self._transactions = transactions
        self._recurring = recurring

    def ensure_system_categories(self) -> Category:
        """Make sure the fallback *Uncategorized* category exists and return it."""
        existing = self._categories.find_by_name(UNCATEGORIZED_NAME)
        if existing is not None:
            return existing
        fallback = Category.create(UNCATEGORIZED_NAME, "#94a3b8", "circle-help", is_system=True)
        self._categories.add(fallback)
        return fallback

    def list_all(self) -> list[CategoryDetails]:
        """All categories, alphabetical, with system categories last."""
        categories = sorted(
            self._categories.list_all(), key=lambda c: (c.is_system, c.name.lower())
        )
        return [CategoryDetails(c, self._budgets.get(c.id)) for c in categories]

    def get(self, category_id: str) -> CategoryDetails:
        """One category with its budget."""
        category = self._require(category_id)
        return CategoryDetails(category, self._budgets.get(category_id))

    def create(self, data: CategoryInput) -> CategoryDetails:
        """Create a category with an optional monthly limit."""
        category = Category.create(data.name, data.color, data.icon)
        self._ensure_unique_name(category.name, exclude_id=None)
        self._categories.add(category)
        if data.monthly_limit is not None:
            self._budgets.set_limit(category.id, data.monthly_limit)
        return self.get(category.id)

    def update(self, category_id: str, data: CategoryInput) -> CategoryDetails:
        """Edit a category; passing no limit removes its budget."""
        existing = self._require(category_id)
        updated = Category(
            id=existing.id,
            name=data.name,
            color=data.color,
            icon=data.icon,
            is_system=existing.is_system,
        )
        if existing.is_system and updated.name != existing.name:
            raise ConflictError("System categories cannot be renamed")
        self._ensure_unique_name(updated.name, exclude_id=category_id)
        self._categories.update(updated)
        if data.monthly_limit is not None:
            self._budgets.set_limit(category_id, data.monthly_limit)
        else:
            self._budgets.remove_limit(category_id)
        return self.get(category_id)

    def delete(self, category_id: str) -> None:
        """Delete a category, moving its transactions to *Uncategorized*."""
        category = self._require(category_id)
        if category.is_system:
            raise ConflictError("System categories cannot be deleted")
        fallback = self.ensure_system_categories()
        self._transactions.reassign_category(category_id, fallback.id)
        self._recurring.reassign_category(category_id, fallback.id)
        self._rules.delete_for_category(category_id)
        self._budgets.remove_limit(category_id)
        self._categories.delete(category_id)

    def _require(self, category_id: str) -> Category:
        category = self._categories.get(category_id)
        if category is None:
            raise NotFoundError("Category", category_id)
        return category

    def _ensure_unique_name(self, name: str, exclude_id: str | None) -> None:
        clash = self._categories.find_by_name(name)
        if clash is not None and clash.id != exclude_id:
            raise ConflictError(f"A category named '{name}' already exists")
