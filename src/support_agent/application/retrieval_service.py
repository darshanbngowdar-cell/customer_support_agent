from support_agent.domain.documents import HybridRetrievalResult
from support_agent.infrastructure.retrievers.hybrid import HybridRetriever


class RetrievalService:
    """Application service for configurable hybrid knowledge retrieval."""

    def __init__(self, retriever: HybridRetriever) -> None:
        self._retriever = retriever

    def retrieve(self, query: str) -> HybridRetrievalResult:
        return self._retriever.search(query)
