import pytest

from support_agent.domain.exceptions import DependencyInitializationError, LLMRequestError
from support_agent.infrastructure.llm.openai_client import OpenAIClient


def test_openai_client_raises_when_dependency_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "support_agent.infrastructure.llm.openai_client.import_module",
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError()),
    )

    with pytest.raises(DependencyInitializationError) as exc_info:
        OpenAIClient(api_key="key")

    assert "openai package is required" in str(exc_info.value).lower()


def test_openai_client_wraps_api_errors(monkeypatch) -> None:
    class MockChatCompletion:
        @staticmethod
        def create(*args, **kwargs):
            raise RuntimeError("service unavailable")

    class FakeOpenAI:
        api_key = None
        ChatCompletion = MockChatCompletion

    monkeypatch.setattr(
        "support_agent.infrastructure.llm.openai_client.import_module",
        lambda name: FakeOpenAI(),
    )

    client = OpenAIClient(api_key="key")

    with pytest.raises(LLMRequestError):
        client.generate("sys", "usr")
