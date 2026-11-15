"""Chain of Responsibility: automatic expense categorisation.

``CategorizationHandler`` is the abstract *Handler*. Each concrete handler
either answers a :class:`CategorizationRequest` or passes it to its
successor. The default chain is::

    KeywordRuleHandler → MerchantRuleHandler → UserDefinedRuleHandler → DefaultCategoryHandler

The order is configuration (see ``CATEGORIZATION_ORDER`` in settings and
:class:`CategorizationChainBuilder`), not code: handlers do not know who
follows them, so they can be re-ordered, removed or extended freely.
Every handler honours the same contract, so any can stand in for another
(Liskov). Handlers depend only on tiny read-only ports defined here
(Interface Segregation), not on whole repositories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import ClassVar, Protocol

from app.domain.category import UNCATEGORIZED_NAME, Category
from app.domain.category_rule import CategoryRule, contains_term
from app.domain.errors import DomainError, DomainValidationError
from app.domain.transaction import normalize_description

# --- Narrow ports (Interface Segregation) -----------------------------------


class KeywordRuleSource(Protocol):
    """Read access to user-managed keyword rules."""

    def list_rules(self) -> Sequence[CategoryRule]:
        """Return every keyword rule."""
        ...


class CategoryNameLookup(Protocol):
    """Look a category up by its name."""

    def find_by_name(self, name: str) -> Category | None:
        """Return the category with that name (case-insensitive) or None."""
        ...


class CategorizationHistory(Protocol):
    """Read access to the user's own past manual categorisations."""

    def latest_manual_category_for(self, normalized_description: str) -> str | None:
        """Category id the user most recently chose for this exact description."""
        ...


# --- Request / result -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CategorizationRequest:
    """The description to categorise."""

    description: str

    @property
    def normalized(self) -> str:
        """Trimmed, lower-cased description."""
        return normalize_description(self.description)


@dataclass(frozen=True, slots=True)
class CategorizationResult:
    """The chosen category, which handler chose it, and a human-readable reason."""

    category_id: str
    matched_by: str
    reason: str


# --- Abstract handler -------------------------------------------------------


class CategorizationHandler(ABC):
    """Abstract handler of the chain.

    :meth:`handle` is a Template Method: it tries :meth:`_try_handle` and
    forwards to the successor when this handler cannot decide.
    """

    name: ClassVar[str]

    def __init__(self) -> None:
        self._next: CategorizationHandler | None = None

    def set_next(self, handler: CategorizationHandler) -> CategorizationHandler:
        """Link ``handler`` as successor and return it, allowing fluent chaining."""
        self._next = handler
        return handler

    def handle(self, request: CategorizationRequest) -> CategorizationResult | None:
        """Answer the request or delegate it down the chain."""
        result = self._try_handle(request)
        if result is not None:
            return result
        return self._next.handle(request) if self._next is not None else None

    @abstractmethod
    def _try_handle(self, request: CategorizationRequest) -> CategorizationResult | None:
        """Return a result when this handler can categorise the request."""


# --- Concrete handlers ------------------------------------------------------


class KeywordRuleHandler(CategorizationHandler):
    """Matches user-managed keyword rules ("Uber" → Transport).

    When several keywords match, the longest (most specific) wins, so
    "uber eats" beats "uber".
    """

    name = "keyword"

    def __init__(self, rules: KeywordRuleSource) -> None:
        super().__init__()
        self._rules = rules

    def _try_handle(self, request: CategorizationRequest) -> CategorizationResult | None:
        matches = [rule for rule in self._rules.list_rules() if rule.matches(request.description)]
        if not matches:
            return None
        best = max(matches, key=lambda rule: len(rule.keyword))
        return CategorizationResult(best.category_id, self.name, f'keyword "{best.keyword}"')


@dataclass(frozen=True, slots=True)
class MerchantProfile:
    """A known merchant: its category and the aliases it appears under on statements."""

    category_name: str
    aliases: tuple[str, ...]


class MerchantRuleHandler(CategorizationHandler):
    """Recognises well-known merchants from bank-statement style text.

    Statements say things like ``POS 4411 AMZN MKTP`` rather than "Amazon";
    the merchant directory maps such aliases to a canonical merchant and its
    category. The longest matching alias wins ("amazon prime" beats
    "amazon"). The directory is injected data, so it can come from a file,
    a database or a remote service without changing this class.
    """

    name = "merchant"

    def __init__(
        self, directory: Mapping[str, MerchantProfile], categories: CategoryNameLookup
    ) -> None:
        super().__init__()
        self._directory = directory
        self._categories = categories

    def _try_handle(self, request: CategorizationRequest) -> CategorizationResult | None:
        matches = [
            (len(alias), merchant, profile)
            for merchant, profile in self._directory.items()
            for alias in profile.aliases
            if contains_term(request.description, alias)
        ]
        for _, merchant, profile in sorted(matches, key=lambda match: match[0], reverse=True):
            category = self._categories.find_by_name(profile.category_name)
            if category is not None:
                return CategorizationResult(category.id, self.name, f"merchant {merchant}")
        return None


class UserDefinedRuleHandler(CategorizationHandler):
    """Applies rules the user defined through their own past choices.

    If the user once filed "Sharma Dairy" under *Food & Dining* by hand,
    the next "Sharma Dairy" expense goes there automatically. Only manual
    choices count, so the system never reinforces its own guesses.
    """

    name = "user_defined"

    def __init__(self, history: CategorizationHistory) -> None:
        super().__init__()
        self._history = history

    def _try_handle(self, request: CategorizationRequest) -> CategorizationResult | None:
        category_id = self._history.latest_manual_category_for(request.normalized)
        if category_id is None:
            return None
        return CategorizationResult(
            category_id, self.name, "your earlier choice for this description"
        )


class DefaultCategoryHandler(CategorizationHandler):
    """Terminal handler: always answers with the fallback category."""

    name = "default"

    def __init__(
        self, categories: CategoryNameLookup, fallback_name: str = UNCATEGORIZED_NAME
    ) -> None:
        super().__init__()
        self._categories = categories
        self._fallback_name = fallback_name

    def _try_handle(
        self,
        request: CategorizationRequest,  # noqa: ARG002 - terminal handler ignores the input
    ) -> CategorizationResult | None:
        category = self._categories.find_by_name(self._fallback_name)
        if category is None:
            raise DomainError(f"Fallback category '{self._fallback_name}' does not exist")
        return CategorizationResult(category.id, self.name, "no rule matched")


# --- Builder ----------------------------------------------------------------


class CategorizationChainBuilder:
    """Builder that links handlers in the given order and validates the result.

    Guarantees the chain is non-empty and ends with a
    :class:`DefaultCategoryHandler`, so categorisation always produces an
    answer.
    """

    def __init__(self) -> None:
        self._handlers: list[CategorizationHandler] = []

    def add(self, handler: CategorizationHandler) -> CategorizationChainBuilder:
        """Append a handler to the end of the chain."""
        self._handlers.append(handler)
        return self

    def build(self) -> CategorizationHandler:
        """Link the handlers and return the head of the chain."""
        if not self._handlers:
            raise DomainValidationError("A categorisation chain needs at least one handler")
        if not isinstance(self._handlers[-1], DefaultCategoryHandler):
            raise DomainValidationError("The last handler must be the default fallback")
        for current, successor in zip(self._handlers, self._handlers[1:], strict=False):
            current.set_next(successor)
        return self._handlers[0]
