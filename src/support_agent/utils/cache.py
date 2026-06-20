from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TimedLRUCache(Generic[K, V]):
    """A simple TTL-backed least-recently-used cache for in-process reuse."""

    def __init__(self, maxsize: int = 256, ttl_seconds: int = 300) -> None:
        self._maxsize = maxsize
        self._ttl_seconds = ttl_seconds
        self._cache: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            timestamp, value = entry
            if time.monotonic() - timestamp > self._ttl_seconds:
                self._cache.pop(key, None)
                return None
            self._cache.move_to_end(key)
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (time.monotonic(), value)
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
