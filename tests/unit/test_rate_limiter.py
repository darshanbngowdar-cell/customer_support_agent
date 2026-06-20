import time

import pytest

from support_agent.domain.exceptions import RateLimitExceededError
from support_agent.utils.rate_limiter import RateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    limiter.validate("session-1")
    limiter.validate("session-1")

    with pytest.raises(RateLimitExceededError):
        limiter.validate("session-1")


def test_rate_limiter_resets_after_window() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=1)

    limiter.validate("session-2")
    time.sleep(1.1)
    limiter.validate("session-2")
