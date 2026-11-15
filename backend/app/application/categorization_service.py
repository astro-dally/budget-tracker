"""Use case: categorise a description via the Chain of Responsibility."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import CategoryRepository
from app.domain.categorization import (
    CategorizationHandler,
    CategorizationRequest,
    CategorizationResult,
)
from app.domain.category import Category
from app.domain.errors import DomainError, DomainValidationError, NotFoundError


@dataclass(frozen=True, slots=True)
class CategorySuggestion:
    """A suggested category with an explanation, shown live in the UI."""

    category: Category
    matched_by: str
    reason: str


class CategorizationService:
    """Client of the categorisation chain; knows only the head handler."""

    def __init__(self, chain: CategorizationHandler, categories: CategoryRepository) -> None:
        self._chain = chain
        self._categories = categories

    def categorize(self, description: str) -> CategorizationResult:
        """Run the chain and return its answer."""
        result = self._chain.handle(CategorizationRequest(description))
        if result is None:
            raise DomainError("The categorisation chain must end with a default handler")
        return result

    def suggest(self, description: str) -> CategorySuggestion:
        """Return the category the chain would pick, with its reason."""
        if not description.strip():
            raise DomainValidationError("Description must not be empty")
        result = self.categorize(description)
        category = self._categories.get(result.category_id)
        if category is None:
            raise NotFoundError("Category", result.category_id)
        return CategorySuggestion(category, result.matched_by, result.reason)
