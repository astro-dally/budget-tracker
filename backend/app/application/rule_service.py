"""Use cases: manage keyword categorisation rules."""

from __future__ import annotations

from app.application.ports import CategoryRepository, CategoryRuleRepository
from app.domain.category_rule import CategoryRule
from app.domain.errors import ConflictError, NotFoundError


class RuleService:
    """CRUD for keyword rules consumed by :class:`~app.domain.categorization.KeywordRuleHandler`."""

    def __init__(self, rules: CategoryRuleRepository, categories: CategoryRepository) -> None:
        self._rules = rules
        self._categories = categories

    def list_all(self) -> list[CategoryRule]:
        """All rules sorted by keyword."""
        return sorted(self._rules.list_rules(), key=lambda rule: rule.keyword)

    def create(self, keyword: str, category_id: str) -> CategoryRule:
        """Add a rule; keywords are unique (case-insensitive)."""
        rule = CategoryRule.create(keyword, category_id)
        self._validate(rule, exclude_id=None)
        self._rules.add(rule)
        return rule

    def update(self, rule_id: str, keyword: str, category_id: str) -> CategoryRule:
        """Change a rule's keyword or category."""
        if self._rules.get(rule_id) is None:
            raise NotFoundError("Rule", rule_id)
        rule = CategoryRule(id=rule_id, keyword=keyword, category_id=category_id)
        self._validate(rule, exclude_id=rule_id)
        self._rules.update(rule)
        return rule

    def delete(self, rule_id: str) -> None:
        """Remove a rule."""
        if self._rules.get(rule_id) is None:
            raise NotFoundError("Rule", rule_id)
        self._rules.delete(rule_id)

    def _validate(self, rule: CategoryRule, exclude_id: str | None) -> None:
        if self._categories.get(rule.category_id) is None:
            raise NotFoundError("Category", rule.category_id)
        clash = self._rules.find_by_keyword(rule.keyword)
        if clash is not None and clash.id != exclude_id:
            raise ConflictError(f"A rule for '{rule.keyword}' already exists")
