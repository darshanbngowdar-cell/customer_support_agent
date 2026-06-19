from support_agent.domain.documents import HybridRetrievalResult
from support_agent.infrastructure.retrievers.bm25 import BM25Retriever
from support_agent.infrastructure.retrievers.fusion import ReciprocalRankFusion
from support_agent.infrastructure.vectorstores.base import VectorStore


class HybridRetriever:
    """Coordinates dense retrieval, BM25 retrieval, and reciprocal rank fusion."""

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever,
        fusion: ReciprocalRankFusion,
        dense_top_k: int,
        bm25_top_k: int,
        fusion_top_k: int,
    ) -> None:
        self._vector_store = vector_store
        self._bm25_retriever = bm25_retriever
        self._fusion = fusion
        self._dense_top_k = dense_top_k
        self._bm25_top_k = bm25_top_k
        self._fusion_top_k = fusion_top_k

    def search(self, query: str) -> HybridRetrievalResult:
        dense_results = self._vector_store.similarity_search(query, top_k=self._dense_top_k)
        bm25_results = self._bm25_retriever.search(query, top_k=self._bm25_top_k)
        return self._fusion.fuse(dense_results, bm25_results, top_k=self._fusion_top_k)
