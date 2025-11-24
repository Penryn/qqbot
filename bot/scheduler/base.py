import asyncio
import contextlib
from typing import Awaitable, Callable, Dict

from ..config import DEBUG

PeriodicCallable = Callable[[], Awaitable[None]]


class Scheduler:
    """
    Lightweight async scheduler for periodic background jobs.

    - Add jobs with `add_periodic(name, interval_seconds, coro_func)`.
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

        # Cancel existing job with the same name
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
