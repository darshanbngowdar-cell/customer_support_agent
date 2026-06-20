import time

from support_agent.utils.cache import TimedLRUCache


def test_timed_lru_cache_stores_and_retrieves_values() -> None:
    cache = TimedLRUCache(maxsize=2, ttl_seconds=1)
    cache.set("a", 1)
    cache.set("b", 2)

    assert cache.get("a") == 1
    assert cache.get("b") == 2


def test_timed_lru_cache_evicts_old_items() -> None:
    cache = TimedLRUCache[str, int](maxsize=1, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)

    assert cache.get("a") is None
    assert cache.get("b") == 2


def test_timed_lru_cache_applies_ttl() -> None:
    cache = TimedLRUCache[str, int](maxsize=2, ttl_seconds=0.01)
    cache.set("a", 1)
    time.sleep(0.05)

    assert cache.get("a") is None
