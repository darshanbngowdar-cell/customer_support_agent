from __future__ import annotations

import json
import os
from typing import List

from support_agent.domain.documents import RetrievedChunk, SupportDocumentChunk
from support_agent.infrastructure.vectorstores.base import VectorStore


class InMemoryVectorStore(VectorStore):
    """A minimal in-memory vector store used for demos and tests.

    Scoring is a simple token-overlap heuristic; not suitable for production.
    Optionally persists chunk metadata to a JSON file so a demo can be reloaded.
    """

    def __init__(self, persist_path: str | None = None) -> None:
        self._chunks: List[SupportDocumentChunk] = []
        self._persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            try:
                with open(persist_path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                for item in raw:
                    self._chunks.append(SupportDocumentChunk.model_validate(item))
            except Exception:
                # ignore load errors for demo fallback
                self._chunks = []

    def add_chunks(self, chunks: List[SupportDocumentChunk]) -> int:
        added = 0
        existing_ids = {c.chunk_id for c in self._chunks}
        for chunk in chunks:
            if chunk.chunk_id in existing_ids:
                continue
            self._chunks.append(chunk)
            existing_ids.add(chunk.chunk_id)
            added += 1
        if self._persist_path:
            try:
                with open(self._persist_path, "w", encoding="utf-8") as fh:
                    json.dump([c.model_dump() for c in self._chunks], fh, indent=2)
            except Exception:
                pass
        return added

    def similarity_search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        def normalize_token(t: str) -> str:
            tok = "".join(ch for ch in t.lower() if ch.isalnum())
            if tok.endswith("s") and len(tok) > 3:
                tok = tok[:-1]
            return tok

        query_tokens = {normalize_token(t) for t in query.split() if t.strip()}
        results: List[RetrievedChunk] = []
        for chunk in self._chunks:
            text_tokens = {normalize_token(t) for t in chunk.text.split() if t.strip()}
            if not text_tokens:
                continue
            overlap = len(query_tokens & text_tokens)
            score = overlap / max(len(query_tokens), 1)
            if score <= 0:
                continue
            results.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=round(float(score), 6),
                    retrieval_method="inmemory",
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def list_chunks(self) -> List[SupportDocumentChunk]:
        return list(self._chunks)
