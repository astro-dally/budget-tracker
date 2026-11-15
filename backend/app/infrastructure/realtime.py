"""In-process publish/subscribe hub that feeds the Server-Sent Events stream.

Each user has a private topic: an alert is only ever delivered to the
connections of the user who owns it.

Alerts are raised in worker threads (sync request handlers, the scheduler)
while SSE clients wait on the asyncio event loop. ``publish`` is therefore
thread-safe: it hands each alert to the loop with ``call_soon_threadsafe``.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading

from app.domain.alert import Alert


class Subscription:
    """One connected client's queue of alerts."""

    def __init__(self, user_id: str, queue: asyncio.Queue[Alert], hub: AlertBroadcaster) -> None:
        self._user_id = user_id
        self._queue = queue
        self._hub = hub

    async def get(self, timeout: float) -> Alert | None:
        """Wait up to ``timeout`` seconds for the next alert; None on timeout."""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout)
        except TimeoutError:
            return None

    def close(self) -> None:
        """Stop receiving alerts."""
        self._hub.unsubscribe(self._user_id, self._queue)


class AlertBroadcaster:
    """Fans alerts out to the live SSE connections of the alert's owner."""

    def __init__(self, max_queue_size: int = 100) -> None:
        self._max_queue_size = max_queue_size
        self._subscribers: dict[str, set[asyncio.Queue[Alert]]] = {}
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Remember the event loop that owns the subscriber queues."""
        self._loop = loop

    @property
    def subscriber_count(self) -> int:
        """Number of connected clients."""
        with self._lock:
            return sum(len(queues) for queues in self._subscribers.values())

    def subscribe(self, user_id: str) -> Subscription:
        """Register a new connection for ``user_id`` (call from the event loop)."""
        queue: asyncio.Queue[Alert] = asyncio.Queue(maxsize=self._max_queue_size)
        with self._lock:
            self._subscribers.setdefault(user_id, set()).add(queue)
        return Subscription(user_id, queue, self)

    def unsubscribe(self, user_id: str, queue: asyncio.Queue[Alert]) -> None:
        """Remove a connection."""
        with self._lock:
            queues = self._subscribers.get(user_id)
            if queues is not None:
                queues.discard(queue)
                if not queues:
                    del self._subscribers[user_id]

    def publish(self, user_id: str, alert: Alert) -> None:
        """Deliver ``alert`` to ``user_id``'s connections; safe to call from any thread."""
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        with self._lock:
            queues = list(self._subscribers.get(user_id, ()))
        for queue in queues:
            loop.call_soon_threadsafe(self._offer, queue, alert)

    @staticmethod
    def _offer(queue: asyncio.Queue[Alert], alert: Alert) -> None:
        with contextlib.suppress(asyncio.QueueFull):
            queue.put_nowait(alert)
