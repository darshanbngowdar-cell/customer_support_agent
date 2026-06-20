from pathlib import Path

import pytest

from support_agent.config.settings import Settings
from support_agent.domain.exceptions import DependencyInitializationError
from support_agent.utils.health import HealthChecker


def test_health_checker_creates_paths(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        data_dir=str(tmp_path / "data"),
        vector_store_dir=str(tmp_path / "vector_store"),
    )
    checker = HealthChecker(settings)

    report = checker.run(deep=False)

    assert report["status"] == "ok"
    assert Path(report["data_dir"]).exists()
    assert Path(report["vector_store_dir"]).exists()


def test_health_checker_deep_requires_openai_key(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        data_dir=str(tmp_path / "data"),
        vector_store_dir=str(tmp_path / "vector_store"),
    )
    checker = HealthChecker(settings)

    with pytest.raises(DependencyInitializationError):
        checker.run(deep=True)
