"""A wrapper that will back off of services that throw
throttling exceptions.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, List, Optional, TypeVar

T = TypeVar("T")


logger = logging.getLogger(__name__)


class BackoffError(Exception):
    pass

    @classmethod
    def after(cls, strategy: "BackoffStrategy") -> "BackoffError":
        # Try as we might, sometimes we fail
        return cls(
            "Potential throttling issue - see inner exception. "
            f"Tried backoff {len(strategy.waits)} times "
            f"up to {strategy.waits[-1]} seconds"
        )


def is_common_throttle_exception(e: Exception) -> bool:
    status_code: Optional[int] = None
    if hasattr(e, "status_code"):
        # e.g. azure.core.exceptions.HttpResponseError
        status_code = int(getattr(e, "status_code"))
    elif hasattr(e, "status"):
        # e.g. aiohttp.client_exceptions.ClientResponseError
        status_code = int(getattr(e, "status"))

    return status_code is not None and (status_code == 503 or status_code == 429)


@dataclass
class BackoffStrategy:
    waits: List[float] = field(default_factory=lambda: [1.0, 2.0, 4.0, 7.0, 16.0])
    """A list of seconds values that a backoff should wait, in order"""

    spread_precentage: float = 0.2
    """The variance around the wait seconds to actually wait.

    Used to introduce some randomness to combat machine synchronization
    """

    def spread(self, seconds: float) -> float:
        """Takes the given time in seconds and picks a random point
        around it defined by the spread percentage. E.g. 6 seconds
        with a 0.2 spread percentage will be between 4.8 and
        7.2 seconds.
        """
        sp = self.spread_precentage
        return seconds * random.uniform(1 - sp, 1 + sp)

    def get_waits(self) -> List[float]:
        """Returns a copy of the waits list"""
        return [self.spread(w) for w in self.waits]


def _warn_throttle(wait_time: float, throttle_exception: Exception) -> None:
    logger.warning(
        f"Service responded with {throttle_exception} - "
        f"trying again in {wait_time:.1f} seeconds..."
    )


def with_backoff(
    fn: Callable[[], T],
    strategy: Optional[BackoffStrategy] = None,
    is_throttle: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """Executes the given function fn. If an exception is raised
    that returns True from is_throttle, wait for a bit and try again,
    or fail after so many retries.
    """
    if strategy is None:
        strategy = BackoffStrategy()

    if is_throttle is None:
        is_throttle = is_common_throttle_exception

    throttle_exception: Optional[Exception] = None

    for next_wait in strategy.get_waits():
        try:

            # Try to do the thing and return
            return fn()

        except Exception as e:
            if is_throttle(e):
                # Backoff for the wait time
                _warn_throttle(next_wait, e)
                time.sleep(next_wait)
                throttle_exception = e
            else:
                raise

    raise BackoffError.after(strategy) from throttle_exception


async def with_backoff_async(
    fn: Callable[[], Coroutine[Any, Any, T]],
    strategy: Optional[BackoffStrategy] = None,
    is_throttle: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """Executes the given function fn. If an exception is raised
    that returns True from is_throttle, wait for a bit and try again,
    or fail after so many retries.
    """
    if strategy is None:
        strategy = BackoffStrategy()

    if is_throttle is None:
        is_throttle = is_common_throttle_exception

    throttle_exception: Optional[Exception] = None

    for next_wait in strategy.get_waits():
        try:

            # Try to do the thing and return
            return await fn()

        except Exception as e:
            if is_throttle(e):
                # Backoff for the wait time
                _warn_throttle(next_wait, e)
                await asyncio.sleep(next_wait)
                throttle_exception = e
            else:
                raise

    raise BackoffError.after(strategy) from throttle_exception
