from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import DefaultDict

from support_agent.domain.exceptions import RateLimitExceededError


class RateLimiter:
    """Simple fixed-window rate limiter keyed by session id."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: DefaultDict[str, deque[float]] = defaultdict(deque)

    def validate(self, session_id: str) -> None:
        now = time.monotonic()
        queue = self._requests[session_id]
        while queue and now - queue[0] >= self.window_seconds:
            queue.popleft()

        if len(queue) >= self.max_requests:
            raise RateLimitExceededError(
                f"Rate limit exceeded for session '{session_id}'. "
                f"Allowed {self.max_requests} requests per {self.window_seconds} seconds."
            )

        queue.append(now)
