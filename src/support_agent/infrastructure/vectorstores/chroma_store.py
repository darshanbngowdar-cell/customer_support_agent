from typing import Any

import chromadb

from support_agent.domain.documents import RetrievedChunk, SupportDocumentChunk
from support_agent.infrastructure.embeddings.base import EmbeddingProvider
from support_agent.infrastructure.vectorstores.base import VectorStore


class ChromaVectorStore(VectorStore):
    """ChromaDB-backed dense vector store with metadata and duplicate protection."""

    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: list[SupportDocumentChunk]) -> int:
        unique_chunks = self._without_existing_duplicates(chunks)
        if not unique_chunks:
            return 0

        embeddings = self._embedding_provider.embed_documents([chunk.text for chunk in unique_chunks])
        self._collection.add(
            ids=[chunk.chunk_id for chunk in unique_chunks],
            documents=[chunk.text for chunk in unique_chunks],
            embeddings=embeddings,
            metadatas=[self._clean_metadata(chunk.metadata | {"content_hash": chunk.content_hash}) for chunk in unique_chunks],
        )
        return len(unique_chunks)

    def similarity_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        query_embedding = self._embedding_provider.embed_query(query)
        raw_results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return self._to_retrieved_chunks(raw_results)

    def list_chunks(self) -> list[SupportDocumentChunk]:
        raw = self._collection.get(include=["documents", "metadatas"])
        chunks: list[SupportDocumentChunk] = []
        ids = raw.get("ids", [])
        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])
        for chunk_id, text, metadata in zip(ids, documents, metadatas, strict=False):
            if text is None:
                continue
            clean_metadata = dict(metadata or {})
            content_hash = str(clean_metadata.pop("content_hash", ""))
            chunks.append(
                SupportDocumentChunk(
                    chunk_id=str(chunk_id),
                    text=text,
                    metadata=clean_metadata,
                    content_hash=content_hash,
                )
            )
        return chunks

    def _without_existing_duplicates(
        self,
        chunks: list[SupportDocumentChunk],
    ) -> list[SupportDocumentChunk]:
        if not chunks:
            return []

        existing = self._collection.get(include=["metadatas"])
        existing_ids = set(existing.get("ids", []))
        existing_hashes = {
            metadata.get("content_hash")
            for metadata in existing.get("metadatas", [])
            if metadata and metadata.get("content_hash")
        }

        unique: list[SupportDocumentChunk] = []
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()
        for chunk in chunks:
            if chunk.chunk_id in existing_ids or chunk.chunk_id in seen_ids:
                continue
            if chunk.content_hash in existing_hashes or chunk.content_hash in seen_hashes:
                continue
            seen_ids.add(chunk.chunk_id)
            seen_hashes.add(chunk.content_hash)
            unique.append(chunk)
        return unique

    def _to_retrieved_chunks(self, raw_results: dict[str, Any]) -> list[RetrievedChunk]:
        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            clean_metadata = dict(metadata or {})
            content_hash = str(clean_metadata.pop("content_hash", ""))
            score = self._distance_to_score(float(distance))
            retrieved.append(
                RetrievedChunk(
                    chunk=SupportDocumentChunk(
                        chunk_id=str(chunk_id),
                        text=text,
                        metadata=clean_metadata,
                        content_hash=content_hash,
                    ),
                    score=score,
                    retrieval_method="dense",
                    source_scores={"distance": float(distance)},
                )
            )
        return retrieved

    @staticmethod
    def _distance_to_score(distance: float) -> float:
        return 1.0 / (1.0 + max(distance, 0.0))

    @staticmethod
    def _clean_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
        cleaned: dict[str, str | int | float | bool] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, str | int | float | bool):
                cleaned[key] = value
            else:
                cleaned[key] = str(value)
        return cleaned
