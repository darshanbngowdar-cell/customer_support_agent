import os

import pytest


@pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="E2E tests disabled")
def test_smoke_container_query():
    # This is a placeholder smoke test that is intended to run in CI when a container is available.
    # It requires RUN_E2E=1 and a running support-agent container reachable at localhost:8000 (example).
    # Implementers should replace this with a real end-to-end scenario.
    assert True
