from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    """A loaded source document before chunking."""

    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupportDocumentChunk(BaseModel):
    """A chunk that can be embedded, indexed, retrieved, and cited."""

    chunk_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str

    @property
    def citation(self) -> str:
        source = str(self.metadata.get("source", "unknown source"))
        page_number = self.metadata.get("page_number")
        section_name = self.metadata.get("section_name")

        if page_number is not None:
            return f"{Path(source).name}, page {page_number}"
        if section_name:
            return f"{Path(source).name}, section {section_name}"
        return Path(source).name


class RetrievedChunk(BaseModel):
    """A retrieved chunk with ranking metadata."""

    chunk: SupportDocumentChunk
    score: float
    retrieval_method: str
    source_scores: dict[str, float] = Field(default_factory=dict)

    @property
    def citation(self) -> str:
        return self.chunk.citation

    def display_payload(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "citation": self.citation,
            "retrieval_method": self.retrieval_method,
            "score": round(self.score, 6),
            "source_scores": {
                key: round(value, 6) for key, value in self.source_scores.items()
            },
            "metadata": self.chunk.metadata,
        }


class HybridRetrievalResult(BaseModel):
    """Full retrieval result, including fused and individual rankings."""

    results: list[RetrievedChunk]
    dense_results: list[RetrievedChunk] = Field(default_factory=list)
    bm25_results: list[RetrievedChunk] = Field(default_factory=list)

    @property
    def citations(self) -> list[str]:
        seen: set[str] = set()
        citations: list[str] = []
        for result in self.results:
            citation = result.citation
            if citation not in seen:
                seen.add(citation)
                citations.append(citation)
        return citations

    @property
    def display_rows(self) -> list[dict[str, object]]:
        return [result.display_payload() for result in self.results]


def stable_content_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def stable_chunk_id(source: str, text: str, chunk_index: int, metadata: dict[str, Any]) -> str:
    page_number = metadata.get("page_number", "")
    section_name = metadata.get("section_name", "")
    raw_id = f"{source}|{page_number}|{section_name}|{chunk_index}|{stable_content_hash(text)}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
