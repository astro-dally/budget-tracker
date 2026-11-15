"""Background job that generates recurring transactions on an interval."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

JOB_ID = "generate-recurring-transactions"


class RecurringTransactionScheduler:
    """Runs a job immediately on start and then every ``interval_minutes``.

    The job itself is idempotent, so overlapping or repeated runs (or a
    restart) can never create duplicates; ``max_instances=1`` and
    ``coalesce=True`` simply avoid wasted work.
    """

    def __init__(self, job: Callable[[], int], interval_minutes: int) -> None:
        self._job = job
        self._interval_minutes = interval_minutes
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        """Schedule the job and start the background thread."""
        self._scheduler.add_job(
            self._run,
            "interval",
            minutes=self._interval_minutes,
            id=JOB_ID,
            next_run_time=datetime.now().astimezone(),
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        self._scheduler.start()

    def shutdown(self) -> None:
        """Stop the scheduler if it is running."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def _run(self) -> None:
        try:
            self._job()
        except Exception:
            logger.exception("Recurring transaction job failed")
