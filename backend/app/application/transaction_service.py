"""Use cases: record, edit, delete and list transactions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.budget_monitor import BudgetMonitor
from app.application.categorization_service import CategorizationService
from app.application.ports import CategoryRepository, TransactionRepository
from app.application.queries import Page, TransactionQuery
from app.domain.enums import CategorySource, TransactionType
from app.domain.errors import DuplicateRecurrenceError, NotFoundError
from app.domain.money import Money
from app.domain.recurrence import RecurringPayment
from app.domain.transaction import Transaction


@dataclass(frozen=True, slots=True)
class TransactionInput:
    """Data needed to create or fully replace a transaction.

    ``category_id=None`` on an expense means "categorise it for me".
    """

    type: TransactionType
    amount: Money
    description: str
    occurred_on: date
    category_id: str | None = None


class TransactionService:
    """Coordinates categorisation, persistence and budget checks for transactions.

    It orchestrates collaborators but owns no business rule itself: the
    chain decides categories, the monitor decides alerts, the entity guards
    its own invariants (SRP).
    """

    def __init__(
        self,
        transactions: TransactionRepository,
        categories: CategoryRepository,
        categorizer: CategorizationService,
        monitor: BudgetMonitor,
    ) -> None:
        self._transactions = transactions
        self._categories = categories
        self._categorizer = categorizer
        self._monitor = monitor

    def get(self, transaction_id: str) -> Transaction:
        """Fetch a transaction or raise :class:`NotFoundError`."""
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise NotFoundError("Transaction", transaction_id)
        return transaction

    def search(self, query: TransactionQuery) -> Page[Transaction]:
        """List transactions with filters, sorting and paging."""
        return self._transactions.search(query)

    def record(self, data: TransactionInput) -> Transaction:
        """Create a transaction, auto-categorising expenses and checking the budget."""
        category_id, source = self._resolve_category(data)
        transaction = Transaction.create(
            type=data.type,
            amount=data.amount,
            description=data.description,
            occurred_on=data.occurred_on,
            category_id=category_id,
            category_source=source,
        )
        self._transactions.add(transaction)
        self._check_budget(transaction)
        return transaction

    def update(self, transaction_id: str, data: TransactionInput) -> Transaction:
        """Replace a transaction and re-check the budget it now belongs to.

        Moving an expense to another category or month, or raising its
        amount, can cross a threshold there; lowering it never re-alerts.
        """
        existing = self.get(transaction_id)
        category_id, source = self._resolve_category(data)
        updated = Transaction(
            id=existing.id,
            type=data.type,
            amount=data.amount,
            description=data.description,
            occurred_on=data.occurred_on,
            category_id=category_id,
            category_source=source,
            recurring_id=existing.recurring_id,
        )
        self._transactions.update(updated)
        self._check_budget(updated)
        return updated

    def delete(self, transaction_id: str) -> None:
        """Delete a transaction (budget usage is recomputed on the next read)."""
        self.get(transaction_id)
        self._transactions.delete(transaction_id)

    def record_recurring(self, payment: RecurringPayment, occurred_on: date) -> bool:
        """Materialise one occurrence of a recurring payment, idempotently.

        Returns False when that occurrence already exists.
        """
        if self._transactions.exists_for_recurrence(payment.id, occurred_on):
            return False
        category_id, source = self._resolve_category(
            TransactionInput(
                type=payment.type,
                amount=payment.amount,
                description=payment.description,
                occurred_on=occurred_on,
                category_id=payment.category_id,
            )
        )
        transaction = Transaction.create(
            type=payment.type,
            amount=payment.amount,
            description=payment.description,
            occurred_on=occurred_on,
            category_id=category_id,
            category_source=source,
            recurring_id=payment.id,
        )
        try:
            self._transactions.add(transaction)
        except DuplicateRecurrenceError:
            return False
        self._check_budget(transaction)
        return True

    def _resolve_category(self, data: TransactionInput) -> tuple[str | None, CategorySource]:
        if data.category_id is not None:
            if self._categories.get(data.category_id) is None:
                raise NotFoundError("Category", data.category_id)
            return data.category_id, CategorySource.MANUAL
        if data.type is TransactionType.EXPENSE:
            return self._categorizer.categorize(data.description).category_id, CategorySource.AUTO
        return None, CategorySource.MANUAL

    def _check_budget(self, transaction: Transaction) -> None:
        if transaction.is_expense and transaction.category_id is not None:
            self._monitor.check(transaction.category_id, transaction.period)
