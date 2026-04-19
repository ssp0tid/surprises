from cachetools import TTLCache
from datetime import datetime
from typing import Any


class CacheService:
    def __init__(self, maxsize: int = 100, ttl: int = 1800):
        self._cache: TTLCache[str, tuple[Any, datetime]] = TTLCache(
            maxsize=maxsize, ttl=ttl
        )
        self._default_ttl = ttl

    def get(self, key: str) -> tuple[Any, bool]:
        if key in self._cache:
            data, _ = self._cache[key]
            return data, True
        return None, False

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._cache[key] = (value, datetime.now())

    def get_stale(self, key: str) -> tuple[Any, bool, datetime | None]:
        if key in self._cache:
            data, cached_at = self._cache[key]
            return data, True, cached_at
        return None, False, None

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

    def has(self, key: str) -> bool:
        return key in self._cache
