from support_agent.infrastructure.llm.base import LLMClient


class MockLLMClient(LLMClient):
    """Deterministic LLM test double."""

    def __init__(self, response: str = "Mock response grounded in the provided context.") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response

    def ping(self) -> bool:
        return True
