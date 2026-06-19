from abc import ABC, abstractmethod

from support_agent.domain.documents import RetrievedChunk, SupportDocumentChunk


class VectorStore(ABC):
    """Interface for dense vector storage and similarity search."""

    @abstractmethod
    def add_chunks(self, chunks: list[SupportDocumentChunk]) -> int:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        raise NotImplementedError

    @abstractmethod
    def list_chunks(self) -> list[SupportDocumentChunk]:
        raise NotImplementedError
