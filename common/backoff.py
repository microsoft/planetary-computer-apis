"""A wrapper that will back off of services that throw
throttling exceptions.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, TypeVar

T = TypeVar("T")


logger = logging.getLogger(__name__)


class BackoffError(Exception):
    pass


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

    for backoff_wait_seconds in strategy.waits:
        try:

            # Try to do the thing and return
            return fn()

        except Exception as e:
            if is_throttle(e):
                # Handle throttling by backing off a random bit
                actual_wait = backoff_wait_seconds * random.uniform(0.8, 1.2)
                logger.warning(
                    f"Service responded with throttling message - "
                    f"trying again in {actual_wait:.1f} seeconds..."
                )
                time.sleep(actual_wait)
                throttle_exception = e
            else:
                raise

    # Try as we might, sometimes we fail
    raise BackoffError(
        "Potential throttling issue - see inner exception. "
        f"Tried backoff {len(strategy.waits)} times "
        f"up to {strategy.waits[-1]} seconds"
    ) from throttle_exception
