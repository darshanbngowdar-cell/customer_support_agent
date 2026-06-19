from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Interface for embedding text for storage and retrieval."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError
