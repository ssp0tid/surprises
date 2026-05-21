"""Retry logic with exponential backoff."""

import asyncio
from typing import Callable, TypeVar

from ..parser.models import RetryConfig


T = TypeVar("T")


class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
    ):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay

    @classmethod
    def from_config(cls, config: RetryConfig | None) -> "RetryPolicy":
        if config is None:
            return cls()
        return cls(
            max_attempts=config.max_attempts,
            backoff_factor=config.backoff_factor,
            initial_delay=config.initial_delay,
        )

    def get_delay(self, attempt: int) -> float:
        return self.initial_delay * (self.backoff_factor ** (attempt - 1))


async def with_retry(
    func: Callable[..., T],
    policy: RetryPolicy,
    *args,
    **kwargs,
) -> T:
    last_exception = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < policy.max_attempts:
                delay = policy.get_delay(attempt)
                await asyncio.sleep(delay)

    raise last_exception
