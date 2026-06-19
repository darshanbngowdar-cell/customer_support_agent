from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk


class ReciprocalRankFusion:
    """Fuse multiple ranked lists using configurable weighted RRF."""

    def __init__(self, rrf_k: int = 60, dense_weight: float = 1.0, bm25_weight: float = 1.0) -> None:
        self._rrf_k = rrf_k
        self._weights = {
            "dense": dense_weight,
            "bm25": bm25_weight,
        }

    def fuse(
        self,
        dense_results: list[RetrievedChunk],
        bm25_results: list[RetrievedChunk],
        top_k: int,
    ) -> HybridRetrievalResult:
        fused_scores: dict[str, float] = {}
        best_result_by_id: dict[str, RetrievedChunk] = {}
        source_scores: dict[str, dict[str, float]] = {}

        for method, results in (("dense", dense_results), ("bm25", bm25_results)):
            weight = self._weights.get(method, 1.0)
            for rank, result in enumerate(results, start=1):
                chunk_id = result.chunk.chunk_id
                fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + weight / (self._rrf_k + rank)
                source_scores.setdefault(chunk_id, {})[method] = result.score
                existing = best_result_by_id.get(chunk_id)
                if existing is None or result.score > existing.score:
                    best_result_by_id[chunk_id] = result

        fused_results = []
        for chunk_id, score in fused_scores.items():
            base_result = best_result_by_id[chunk_id]
            fused_results.append(
                RetrievedChunk(
                    chunk=base_result.chunk,
                    score=score,
                    retrieval_method="hybrid_rrf",
                    source_scores=source_scores.get(chunk_id, {}),
                )
            )

        fused_results.sort(key=lambda item: item.score, reverse=True)
        return HybridRetrievalResult(
            results=fused_results[:top_k],
            dense_results=dense_results,
            bm25_results=bm25_results,
        )
