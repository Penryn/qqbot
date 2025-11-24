import asyncio
import contextlib
from datetime import datetime
from typing import Awaitable, Callable, Dict

from croniter import croniter

from ..config import DEBUG

PeriodicCallable = Callable[[], Awaitable[None]]


class Scheduler:
    """
    Lightweight async scheduler for periodic background jobs.

    - Add jobs with `add_periodic(name, interval_seconds, coro_func)`.
    - Add cron-based jobs with `add_cron(name, cron_expr, coro_func)`.
    - Call `stop()` on shutdown to cancel all jobs gracefully.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, asyncio.Task[None]] = {}

    def add_periodic(self, name: str, interval_seconds: float, func: PeriodicCallable) -> None:
        """Start a periodic job that runs `func` every `interval_seconds` seconds."""

        async def runner() -> None:
            try:
                while True:
                    try:
                        await func()
                    except Exception as e:  # noqa: BLE001
                        if DEBUG:
                            print(f"[scheduler] job {name} error: {e!r}")
                    await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                raise

        self._start_task(name, runner)

    def add_cron(self, name: str, cron_expr: str, func: PeriodicCallable) -> None:
        """Start a cron-based job. `cron_expr` follows standard 5-field cron syntax."""

        # Validate expression early
        croniter(cron_expr, datetime.now())

        async def runner() -> None:
            itr = croniter(cron_expr, datetime.now())
            try:
                while True:
                    next_run = itr.get_next(datetime)
                    delay = max(0.0, (next_run - datetime.now()).total_seconds())
                    if delay:
                        await asyncio.sleep(delay)
                    try:
                        await func()
                    except Exception as e:  # noqa: BLE001
                        if DEBUG:
                            print(f"[scheduler] job {name} error: {e!r}")
            except asyncio.CancelledError:
                raise

        self._start_task(name, runner)

    def _start_task(self, name: str, runner: PeriodicCallable) -> None:
        """Cancel existing job with the same name and start a new task."""

        if name in self._tasks:
            self._tasks[name].cancel()

        self._tasks[name] = asyncio.create_task(runner(), name=name)

    async def stop(self) -> None:
        """Cancel all scheduled jobs."""

        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()
