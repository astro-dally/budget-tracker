"""Recurring payments: schedules, generation and idempotency."""

from datetime import date, timedelta

import pytest

from app.application.recurring_service import RecurringInput, RecurringService
from app.domain.category import Category
from app.domain.enums import CategorySource, Frequency, TransactionType
from app.domain.errors import DomainValidationError, DuplicateRecurrenceError
from app.domain.money import Money
from app.domain.recurrence import RecurrenceSchedule
from app.domain.transaction import Transaction
from tests.conftest import World


class TestSchedule:
    def test_daily(self) -> None:
        s = RecurrenceSchedule(Frequency.DAILY, date(2026, 1, 30))
        assert s.occurrences_between(None, date(2026, 2, 2)) == [
            date(2026, 1, 30),
            date(2026, 1, 31),
            date(2026, 2, 1),
            date(2026, 2, 2),
        ]

    def test_weekly_after_a_mark(self) -> None:
        s = RecurrenceSchedule(Frequency.WEEKLY, date(2026, 1, 1))
        assert s.occurrences_between(date(2026, 1, 8), date(2026, 1, 29)) == [
            date(2026, 1, 15),
            date(2026, 1, 22),
            date(2026, 1, 29),
        ]

    def test_monthly_clamps_and_re_anchors(self) -> None:
        s = RecurrenceSchedule(Frequency.MONTHLY, date(2026, 1, 31))
        assert s.occurrences_between(None, date(2026, 4, 30)) == [
            date(2026, 1, 31),
            date(2026, 2, 28),
            date(2026, 3, 31),
            date(2026, 4, 30),
        ]

    def test_end_date_is_respected(self) -> None:
        s = RecurrenceSchedule(Frequency.DAILY, date(2026, 1, 1), date(2026, 1, 3))
        assert len(s.occurrences_between(None, date(2026, 12, 31))) == 3
        assert s.next_on_or_after(date(2026, 1, 4)) is None

    def test_end_before_start_is_invalid(self) -> None:
        with pytest.raises(DomainValidationError):
            RecurrenceSchedule(Frequency.DAILY, date(2026, 1, 2), date(2026, 1, 1))

    def test_next_on_or_after(self) -> None:
        s = RecurrenceSchedule(Frequency.MONTHLY, date(2026, 1, 15))
        assert s.next_on_or_after(date(2026, 3, 15)) == date(2026, 3, 15)
        assert s.next_on_or_after(date(2026, 3, 16)) == date(2026, 4, 15)


def _rent(world: World, start: date, frequency: Frequency = Frequency.MONTHLY) -> RecurringInput:
    housing = world.category("Housing", 30000)
    return RecurringInput(
        "Rent", Money.of(20000), TransactionType.EXPENSE, frequency, start, category_id=housing.id
    )


def _generated(world: World) -> list[Transaction]:
    return [t for t in world.transactions_repo.items.values() if t.recurring_id]


def test_creation_backfills_due_occurrences(world: World) -> None:
    world.recurring.create(_rent(world, date(2026, 9, 1)))
    assert sorted(t.occurred_on for t in _generated(world)) == [
        date(2026, 9, 1),
        date(2026, 10, 1),
        date(2026, 11, 1),
    ]


def test_generation_is_idempotent_across_runs_and_restarts(world: World) -> None:
    world.recurring.create(_rent(world, date(2026, 9, 1), Frequency.WEEKLY))
    count = len(_generated(world))
    assert world.recurring.generate_due() == 0
    restarted = RecurringService(
        world.recurring_repo, world.categories_repo, world.transactions, world.clock
    )
    assert restarted.generate_due() == 0
    assert len(_generated(world)) == count


def test_lost_generation_mark_does_not_duplicate(world: World) -> None:
    """Simulates a crash after inserting transactions but before saving the mark."""
    payment = world.recurring.create(_rent(world, date(2026, 9, 1)))
    world.recurring_repo.items[payment.id] = payment.generated_through(date(2026, 8, 31))
    assert world.recurring.generate_due() == 0
    assert len(_generated(world)) == 3


def test_store_rejects_duplicate_occurrences(world: World) -> None:
    payment = world.recurring.create(_rent(world, date(2026, 11, 1)))
    duplicate = Transaction.create(
        type=TransactionType.EXPENSE,
        amount=Money.of(1),
        description="Rent",
        occurred_on=date(2026, 11, 1),
        category_id=None,
        category_source=CategorySource.AUTO,
        recurring_id=payment.id,
    )
    with pytest.raises(DuplicateRecurrenceError):
        world.transactions_repo.add(duplicate)


def test_new_days_generate_new_occurrences(world: World) -> None:
    world.recurring.create(_rent(world, date(2026, 11, 10), Frequency.DAILY))
    assert len(_generated(world)) == 5
    world.clock.advance(3)
    assert world.recurring.generate_due() == 3


def test_pause_stops_and_resume_skips_missed_dates(world: World) -> None:
    payment = world.recurring.create(_rent(world, date(2026, 11, 14), Frequency.DAILY))
    world.recurring.pause(payment.id)
    world.clock.advance(5)
    assert world.recurring.generate_due() == 0
    world.recurring.resume(payment.id)
    assert sorted(t.occurred_on for t in _generated(world)) == [
        date(2026, 11, 14),
        world.clock.today(),
    ]


def test_future_start_generates_nothing_until_due(world: World) -> None:
    payment = world.recurring.create(_rent(world, date(2026, 12, 1)))
    assert _generated(world) == []
    assert world.recurring.upcoming(5)[0].due_on == payment.schedule.start_date
    world.clock.current = date(2026, 12, 1)
    assert world.recurring.generate_due() == 1


def test_generated_expenses_are_categorised_and_budget_checked(world: World) -> None:
    subs: Category = world.category("Subscriptions", 500)
    world.rules.create("netflix", subs.id)
    world.recurring.create(
        RecurringInput(
            "Netflix",
            Money.of(649),
            TransactionType.EXPENSE,
            Frequency.MONTHLY,
            date(2026, 11, 5),
        )
    )
    assert _generated(world)[0].category_id == subs.id
    assert [a.rule_key for a in world.channel.sent] == ["percent-80", "percent-100"]


def test_upcoming_is_sorted_by_due_date(world: World) -> None:
    world.recurring.create(_rent(world, date(2026, 1, 20)))
    world.recurring.create(
        RecurringInput(
            "Gym",
            Money.of(1000),
            TransactionType.EXPENSE,
            Frequency.WEEKLY,
            world.clock.today() + timedelta(days=2),
        )
    )
    assert [u.payment.description for u in world.recurring.upcoming(5)] == ["Gym", "Rent"]
