from support_agent.domain.documents import RetrievedChunk, SupportDocumentChunk
from support_agent.infrastructure.retrievers.bm25 import BM25Retriever
from support_agent.infrastructure.retrievers.fusion import ReciprocalRankFusion
from support_agent.infrastructure.retrievers.hybrid import HybridRetriever
from support_agent.infrastructure.vectorstores.base import VectorStore


class DummyVectorStore(VectorStore):
    def __init__(self, chunks: list[SupportDocumentChunk]) -> None:
        self._chunks = chunks

    def add_chunks(self, chunks: list[SupportDocumentChunk]) -> int:
        self._chunks.extend(chunks)
        return len(chunks)

    def similarity_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        return [
            RetrievedChunk(
                chunk=self._chunks[0],
                score=0.9,
                retrieval_method="dense",
            )
        ]

    def list_chunks(self) -> list[SupportDocumentChunk]:
        return list(self._chunks)


def test_hybrid_retriever_fuses_dense_and_bm25_results() -> None:
    chunks = [
        SupportDocumentChunk(
            chunk_id="c1",
            text="Reset password instructions.",
            metadata={"source": "reset.md", "page_number": 1},
            content_hash="hash1",
        ),
        SupportDocumentChunk(
            chunk_id="c2",
            text="Billing and refund policy.",
            metadata={"source": "billing.md", "page_number": 2},
            content_hash="hash2",
        ),
    ]

    vector_store = DummyVectorStore(chunks)
    bm25 = BM25Retriever(chunks)
    fusion = ReciprocalRankFusion(rrf_k=1, dense_weight=1.0, bm25_weight=1.0)
    retriever = HybridRetriever(
        vector_store=vector_store,
        bm25_retriever=bm25,
        fusion=fusion,
        dense_top_k=2,
        bm25_top_k=2,
        fusion_top_k=2,
    )

    result = retriever.search("password reset")

    assert len(result.results) == 1
    assert result.results[0].chunk.chunk_id == "c1"
    assert result.results[0].score > 0


def test_hybrid_retriever_returns_empty_for_blank_query() -> None:
    chunks = [
        SupportDocumentChunk(
            chunk_id="c1",
            text="Some support text.",
            metadata={"source": "source.md"},
            content_hash="hash1",
        )
    ]
    vector_store = DummyVectorStore(chunks)
    bm25 = BM25Retriever(chunks)
    fusion = ReciprocalRankFusion()
    retriever = HybridRetriever(
        vector_store=vector_store,
        bm25_retriever=bm25,
        fusion=fusion,
        dense_top_k=1,
        bm25_top_k=1,
        fusion_top_k=1,
    )

    result = retriever.search("   ")

    assert result.results == []
