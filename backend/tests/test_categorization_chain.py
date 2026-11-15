"""Chain of Responsibility: order, fallback, specificity and configurability."""

import pytest

from app.domain.categorization import (
    CategorizationChainBuilder,
    CategorizationHandler,
    CategorizationRequest,
    DefaultCategoryHandler,
    KeywordRuleHandler,
    MerchantRuleHandler,
    UserDefinedRuleHandler,
)
from app.domain.errors import DomainError, DomainValidationError
from app.infrastructure.merchant_directory import DEFAULT_MERCHANTS
from tests.conftest import World
from tests.fakes import InMemoryCategoryRepository


def _setup(world: World) -> dict[str, str]:
    ids = {
        name: world.category(name).id
        for name in ("Transport", "Shopping", "Food & Dining", "Subscriptions")
    }
    world.rules.create("uber", ids["Transport"])
    world.rules.create("uber eats", ids["Food & Dining"])
    world.rules.create("ola", ids["Transport"])
    return ids


def test_keyword_rule_matches_first(world: World) -> None:
    ids = _setup(world)
    result = world.categorization.categorize("Uber trip to airport")
    assert (result.category_id, result.matched_by) == (ids["Transport"], "keyword")


def test_keyword_beats_merchant_in_default_order(world: World) -> None:
    ids = _setup(world)
    result = world.categorization.categorize("UBER via AMZN pay")
    assert result.category_id == ids["Transport"]


def test_longest_keyword_wins(world: World) -> None:
    ids = _setup(world)
    assert world.categorization.categorize("Uber Eats dinner").category_id == ids["Food & Dining"]


def test_keywords_respect_word_boundaries(world: World) -> None:
    _setup(world)
    assert world.categorization.categorize("Coca-Cola crate").matched_by == "default"


def test_merchant_handler_reads_statement_aliases(world: World) -> None:
    ids = _setup(world)
    result = world.categorization.categorize("POS 4411 AMZN MKTP IN")
    assert (result.category_id, result.matched_by) == (ids["Shopping"], "merchant")


def test_longest_merchant_alias_wins(world: World) -> None:
    ids = _setup(world)
    assert (
        world.categorization.categorize("Amazon Prime renewal").category_id == ids["Subscriptions"]
    )


def test_user_defined_handler_learns_manual_choices_only(world: World) -> None:
    ids = _setup(world)
    food = world.categories_repo.get(ids["Food & Dining"])
    world.spend("120", food, text="Sharma Dairy")
    result = world.categorization.categorize("  sharma   DAIRY ")
    assert (result.category_id, result.matched_by) == (ids["Food & Dining"], "user_defined")


def test_auto_categorised_history_is_not_learned(world: World) -> None:
    _setup(world)
    world.spend("50", None, text="Corner kiosk")
    assert world.categorization.categorize("Corner kiosk").matched_by == "default"


def test_falls_back_to_uncategorized(world: World) -> None:
    _setup(world)
    result = world.categorization.categorize("Something unknown")
    assert result.matched_by == "default"
    assert world.categories_repo.get(result.category_id).name == "Uncategorized"  # type: ignore[union-attr]


def test_order_is_configurable(world: World) -> None:
    """Putting the user-defined handler first lets personal history override keywords."""
    ids = _setup(world)
    food = world.categories_repo.get(ids["Food & Dining"])
    world.spend("300", food, text="Uber office lunch")
    reordered = (
        CategorizationChainBuilder()
        .add(UserDefinedRuleHandler(world.transactions_repo))
        .add(KeywordRuleHandler(world.rules_repo))
        .add(DefaultCategoryHandler(world.categories_repo))
        .build()
    )
    result = reordered.handle(CategorizationRequest("Uber office lunch"))
    assert result is not None
    assert result.category_id == ids["Food & Dining"]


def test_builder_requires_terminal_default() -> None:
    with pytest.raises(DomainValidationError):
        CategorizationChainBuilder().build()
    with pytest.raises(DomainValidationError):
        CategorizationChainBuilder().add(
            MerchantRuleHandler(DEFAULT_MERCHANTS, InMemoryCategoryRepository())
        ).build()


def test_default_handler_fails_loudly_when_fallback_is_missing() -> None:
    with pytest.raises(DomainError):
        DefaultCategoryHandler(InMemoryCategoryRepository()).handle(CategorizationRequest("x"))


def test_every_handler_is_substitutable(world: World) -> None:
    """Liskov: any handler alone returns a result or None, never raises for a miss."""
    _setup(world)
    handlers: list[CategorizationHandler] = [
        KeywordRuleHandler(world.rules_repo),
        MerchantRuleHandler(DEFAULT_MERCHANTS, world.categories_repo),
        UserDefinedRuleHandler(world.transactions_repo),
        DefaultCategoryHandler(world.categories_repo),
    ]
    for handler in handlers:
        result = handler.handle(CategorizationRequest("zzz unmatched"))
        assert result is None or result.matched_by == handler.name
