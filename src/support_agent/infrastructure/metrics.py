from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Generator

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("support_agent_requests_total", "Total requests processed")
REQUEST_LATENCY = Histogram("support_agent_request_latency_seconds", "Request latency seconds")


@contextmanager
def track_request() -> Generator[None, None, None]:
    REQUEST_COUNT.inc()
    start = perf_counter()
    try:
        yield
    finally:
        REQUEST_LATENCY.observe(perf_counter() - start)
