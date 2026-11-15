"""Composition root, configuration and scheduler wiring."""

import threading
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.container import build_categorization_chain, build_channels
from app.domain.user import User
from app.infrastructure.realtime import AlertBroadcaster
from app.infrastructure.scheduler import RecurringTransactionScheduler

USER = User.create(
    email="a@b.dev", name="A", password_hash="x", created_at=datetime(2026, 1, 1, tzinfo=UTC)
)


def settings(**overrides: str) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg, arg-type]


def test_thresholds_are_parsed_and_sorted() -> None:
    assert settings(alert_thresholds="100, 80,90").alert_threshold_list == [
        Decimal(80),
        Decimal(90),
        Decimal(100),
    ]


@pytest.mark.parametrize("value", ["", "abc", "80,-1"])
def test_invalid_thresholds_are_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        settings(alert_thresholds=value)


def test_channels_come_from_configuration() -> None:
    channels = build_channels(
        settings(notification_channels="sms,console"), AlertBroadcaster(), USER
    )
    assert [c.name for c in channels] == ["sms", "console"]


def test_unknown_names_fail_fast_with_a_helpful_message() -> None:
    with pytest.raises(ValueError, match="Known values"):
        build_channels(settings(notification_channels="pigeon"), AlertBroadcaster(), USER)
    with pytest.raises(ValueError, match="categorisation handler"):
        build_categorization_chain(["telepathy"], None)  # type: ignore[arg-type]


def test_scheduler_runs_job_immediately_and_survives_errors() -> None:
    ran = threading.Event()

    def job() -> int:
        ran.set()
        raise RuntimeError("boom")

    scheduler = RecurringTransactionScheduler(job, interval_minutes=60)
    scheduler.start()
    try:
        assert ran.wait(timeout=5)
    finally:
        scheduler.shutdown()
    scheduler.shutdown()
