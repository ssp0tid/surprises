"""Simple LRU cache."""

from collections import OrderedDict
from threading import RLock


class LRUCache:
    """Thread-safe LRU cache."""

    def __init__(self, max_size=10000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = RLock()

    def get(self, key, default=None):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return default

    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self):
        with self.lock:
            self.cache.clear()

    def size(self):
        return len(self.cache)
