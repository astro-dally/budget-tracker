"""Notification channels and the SSE broadcaster."""

import asyncio
import io
import threading
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.alert import Alert
from app.domain.enums import AlertLevel
from app.domain.money import Money, Period
from app.infrastructure.notifications import (
    ConsoleChannel,
    EmailChannel,
    EmailSettings,
    InAppChannel,
    SmsChannel,
)
from app.infrastructure.realtime import AlertBroadcaster


def make_alert(message: str = "Food has used 80% of its budget") -> Alert:
    return Alert.create(
        category_id="c1",
        category_name="Food",
        period=Period(2026, 11),
        rule_key="percent-80",
        level=AlertLevel.WARNING,
        threshold=Decimal(80),
        message=message,
        spent=Money.of(800),
        limit=Money.of(1000),
        created_at=datetime(2026, 11, 14, tzinfo=UTC),
    )


def test_console_channel_writes_to_stream() -> None:
    stream = io.StringIO()
    ConsoleChannel(stream).send(make_alert())
    assert stream.getvalue().startswith("[ALERT:WARNING] Food")


def test_email_channel_builds_message_and_stubs_without_smtp() -> None:
    channel = EmailChannel(EmailSettings(sender="a@x.dev", recipient="b@x.dev"))
    message = channel.build_message(make_alert())
    assert message["Subject"] == "Budget alert: Food (2026-11)"
    channel.send(make_alert())


def test_sms_channel_truncates_to_160_characters() -> None:
    text = SmsChannel.format(make_alert("x" * 300))
    assert len(text) == 160
    SmsChannel("+910000000000").send(make_alert())
    SmsChannel(None).send(make_alert())


class _Collector:
    def __init__(self) -> None:
        self.alerts: list[tuple[str, Alert]] = []

    def publish(self, user_id: str, alert: Alert) -> None:
        self.alerts.append((user_id, alert))


def test_in_app_channel_publishes_to_its_user() -> None:
    collector = _Collector()
    InAppChannel(collector, "user-1").send(make_alert())
    assert [user for user, _ in collector.alerts] == ["user-1"]


def test_broadcaster_delivers_across_threads() -> None:
    async def scenario() -> Alert | None:
        hub = AlertBroadcaster()
        hub.bind_loop(asyncio.get_running_loop())
        subscription = hub.subscribe("u1")
        assert hub.subscriber_count == 1
        threading.Thread(target=hub.publish, args=("u1", make_alert())).start()
        received = await subscription.get(timeout=2)
        subscription.close()
        assert hub.subscriber_count == 0
        return received

    received = asyncio.run(scenario())
    assert received is not None
    assert received.category_name == "Food"


def test_broadcaster_only_reaches_the_owner() -> None:
    async def scenario() -> tuple[Alert | None, Alert | None]:
        hub = AlertBroadcaster()
        hub.bind_loop(asyncio.get_running_loop())
        mine, theirs = hub.subscribe("alice"), hub.subscribe("bob")
        hub.publish("alice", make_alert())
        return await mine.get(timeout=1), await theirs.get(timeout=0.05)

    received, leaked = asyncio.run(scenario())
    assert received is not None
    assert leaked is None


def test_broadcaster_without_loop_is_a_no_op() -> None:
    AlertBroadcaster().publish("u1", make_alert())


def test_subscription_times_out() -> None:
    async def scenario() -> Alert | None:
        hub = AlertBroadcaster()
        hub.bind_loop(asyncio.get_running_loop())
        return await hub.subscribe("u1").get(timeout=0.01)

    assert asyncio.run(scenario()) is None
