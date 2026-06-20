from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Minimal chat-completion interface used by application services."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        raise NotImplementedError
