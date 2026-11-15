"""Observer: alerts fire exactly once per category, rule and month."""

from datetime import date

from app.application.observers import NotificationDispatcher
from app.application.transaction_service import TransactionInput
from app.domain.enums import AlertLevel, TransactionType
from app.domain.money import Money, Period
from tests.conftest import World
from tests.fakes import FailingChannel, RecordingChannel, RecordingObserver


def test_crossing_80_percent_fires_one_warning(world: World) -> None:
    food = world.category("Food", 1000)
    world.spend("500", food)
    assert world.channel.sent == []
    world.spend("300", food)
    assert [a.level for a in world.channel.sent] == [AlertLevel.WARNING]


def test_alert_is_not_repeated_within_the_month(world: World) -> None:
    food = world.category("Food", 1000)
    world.spend("850", food)
    world.spend("50", food)
    world.spend("10", food)
    world.monitor.check(food.id, Period(2026, 11))
    assert len(world.channel.sent) == 1


def test_one_transaction_crossing_both_thresholds_fires_both_in_order(world: World) -> None:
    food = world.category("Food", 1000)
    world.spend("1500", food)
    assert [a.rule_key for a in world.observer.received] == ["percent-80", "percent-100"]
    assert [a.level for a in world.channel.sent] == [AlertLevel.WARNING, AlertLevel.CRITICAL]


def test_month_rollover_resets_alert_state(world: World) -> None:
    food = world.category("Food", 1000)
    world.spend("900", food, on=date(2026, 11, 20))
    world.spend("900", food, on=date(2026, 12, 2))
    assert [str(a.period) for a in world.channel.sent] == ["2026-11", "2026-12"]


def test_no_budget_means_no_alerts(world: World) -> None:
    misc = world.category("Misc")
    world.spend("99999", misc)
    assert world.channel.sent == []


def test_income_never_triggers_alerts(world: World) -> None:
    world.category("Food", 100)
    world.transactions.record(
        TransactionInput(TransactionType.INCOME, Money.of(5000), "Salary", date(2026, 11, 1))
    )
    assert world.channel.sent == []


def test_editing_an_amount_upwards_can_cross_a_threshold(world: World) -> None:
    food = world.category("Food", 1000)
    tx = world.spend("100", food)
    world.transactions.update(
        tx.id,
        TransactionInput(TransactionType.EXPENSE, Money.of(820), "Item", tx.occurred_on, food.id),
    )
    assert [a.rule_key for a in world.channel.sent] == ["percent-80"]


def test_moving_an_expense_to_another_category_checks_that_budget(world: World) -> None:
    food = world.category("Food", 1000)
    fun = world.category("Fun", 100)
    tx = world.spend("150", food)
    world.transactions.update(
        tx.id,
        TransactionInput(TransactionType.EXPENSE, tx.amount, "Concert", tx.occurred_on, fun.id),
    )
    assert {a.category_name for a in world.channel.sent} == {"Fun"}


def test_delete_and_recross_does_not_spam(world: World) -> None:
    food = world.category("Food", 1000)
    tx = world.spend("900", food)
    world.transactions.delete(tx.id)
    assert world.budgets.statuses(Period(2026, 11))[0].usage.spent == Money.zero()
    world.spend("900", food)
    assert len(world.channel.sent) == 1


def test_lowering_a_limit_raises_alerts_immediately(world: World) -> None:
    food = world.category("Food", 1000)
    world.spend("500", food)
    world.budgets.set_limit(food.id, Money.of(550))
    assert [a.rule_key for a in world.channel.sent] == ["percent-80"]


def test_detached_observers_stop_receiving(world: World) -> None:
    food = world.category("Food", 100)
    world.monitor.detach(world.observer)
    world.monitor.detach(world.observer)
    world.spend("90", food)
    assert world.observer.received == []
    assert len(world.channel.sent) == 1


def test_attach_is_idempotent(world: World) -> None:
    extra = RecordingObserver()
    world.monitor.attach(extra)
    world.monitor.attach(extra)
    world.spend("90", world.category("Food", 100))
    assert len(extra.received) == 1


def test_failing_channel_does_not_block_others(world: World) -> None:
    good = RecordingChannel()
    world.monitor.attach(NotificationDispatcher([FailingChannel(), good]))
    world.spend("90", world.category("Food", 100))
    assert len(good.sent) == 1
