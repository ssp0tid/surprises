"""Caching utilities for expensive computations."""

import hashlib
import json
import time
from typing import Any, Optional, Dict
from functools import wraps

from flask import current_app


class Cache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL in seconds."""
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache


def cached(prefix: str, ttl: Optional[int] = None):
    """Decorator to cache function results.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (uses default if not specified)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_app.config.get("CACHE_ENABLED", True):
                return func(*args, **kwargs)

            cache = get_cache()
            cache_key = cache._make_key(prefix, *args, **kwargs)

            if ttl is None:
                ttl = current_app.config.get("CACHE_TTL", {}).get(prefix, 60)

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: str = None):
    """Invalidate cache entries."""
    if prefix is None:
        get_cache().clear()
