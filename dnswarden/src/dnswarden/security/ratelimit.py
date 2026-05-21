"""Rate limiter using token bucket algorithm."""

import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter per client IP.

    Limits:
    - queries_per_second: Maximum queries per second
    - burst: Maximum burst (tokens in bucket)
    """

    def __init__(self, queries_per_second=100, burst=200):
        self.rate = queries_per_second
        self.burst = burst
        self.buckets = defaultdict(lambda: burst)
        self.last_update = defaultdict(lambda: time.time())

    def allow(self, client_ip):
        """Check if query is allowed."""
        now = time.time()
        bucket = self.buckets[client_ip]
        last = self.last_update[client_ip]

        elapsed = now - last
        bucket = min(self.burst, bucket + elapsed * self.rate)

        if bucket >= 1:
            self.buckets[client_ip] = bucket - 1
            self.last_update[client_ip] = now
            return True

        return False

    def clear(self):
        """Clear all rate limit state."""
        self.buckets.clear()
        self.last_update.clear()
