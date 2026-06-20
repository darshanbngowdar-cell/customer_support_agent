from __future__ import annotations

from typing import List, Tuple

try:
    from sentence_transformers import CrossEncoder
except Exception:  # pragma: no cover - optional dependency
    CrossEncoder = None


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        if CrossEncoder is None:
            raise RuntimeError("CrossEncoder not available. Install sentence-transformers with cross-encoder support.")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Candidates is list of (doc_text, score). Returns same format sorted by reranker score."""
        pairs = [[query, text] for text, _ in candidates]
        scores = self.model.predict(pairs)
        combined = list(zip([t for t, _ in candidates], scores))
        combined.sort(key=lambda x: x[1], reverse=True)
        return combined
