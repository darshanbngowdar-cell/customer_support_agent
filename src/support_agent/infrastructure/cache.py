from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Optional

try:
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None


class CacheBase:
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError()

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError()


class InMemoryLRUCache(CacheBase):
    def __init__(self, max_items: int = 256) -> None:
        self.max_items = max_items
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        # move to end for LRU
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if key in self._store:
            del self._store[key]
        expires_at = time.time() + ttl_seconds if ttl_seconds else 0
        self._store[key] = (expires_at, value)
        if len(self._store) > self.max_items:
            self._store.popitem(last=False)


class RedisCache(CacheBase):
    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        if redis is None:
            raise RuntimeError("redis package is not installed")
        self._client = redis.Redis.from_url(url)

    def get(self, key: str) -> Optional[Any]:
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            return raw.decode("utf-8")
        except Exception:
            return raw

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if ttl_seconds:
            self._client.setex(key, ttl_seconds, str(value))
        else:
            self._client.set(key, str(value))
