from __future__ import annotations

from pathlib import Path

from support_agent.config.settings import Settings
from support_agent.domain.exceptions import DependencyInitializationError
from support_agent.infrastructure.llm import OpenAIClient


class HealthChecker:
    """Health checks for environment, storage, and optional LLM dependencies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def run(self, deep: bool = False) -> dict[str, object]:
        report: dict[str, object] = {
            "status": "ok",
            "environment": self._settings.app_env,
            "data_dir": str(self._settings.data_dir),
            "vector_store_dir": str(self._settings.vector_store_dir),
        }

        self._ensure_directory(self._settings.data_dir)
        self._ensure_directory(self._settings.vector_store_dir)

        if deep:
            if self._settings.openai_api_key is None:
                raise DependencyInitializationError(
                    "Deep health check requires SUPPORT_AGENT_OPENAI_API_KEY to be configured."
                )
            client = OpenAIClient(
                api_key=self._settings.openai_api_key.get_secret_value(),
                model=self._settings.openai_model,
                timeout=self._settings.openai_request_timeout,
            )
            client.ping()
            report["openai"] = {
                "status": "operational",
                "model": self._settings.openai_model,
            }

        return report

    @staticmethod
    def _ensure_directory(path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DependencyInitializationError(
                f"Unable to create or access path: {path}"
            ) from exc
