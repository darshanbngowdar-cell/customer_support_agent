from pathlib import Path

from support_agent.domain.documents import SourceDocument, SupportDocumentChunk
from support_agent.infrastructure.loaders.chunker import DynamicDocumentChunker
from support_agent.infrastructure.loaders.document_loader import DocumentLoader
from support_agent.infrastructure.vectorstores.base import VectorStore


class IngestionService:
    """Loads, chunks, deduplicates, and indexes knowledge-base documents."""

    def __init__(
        self,
        document_loader: DocumentLoader,
        chunker: DynamicDocumentChunker,
        vector_store: VectorStore,
    ) -> None:
        self._document_loader = document_loader
        self._chunker = chunker
        self._vector_store = vector_store

    def ingest_directory(self, directory: Path) -> int:
        documents = self.load_documents(directory)
        chunks = self.chunk_documents(documents)
        return self._vector_store.add_chunks(chunks)

    def load_documents(self, directory: Path) -> list[SourceDocument]:
        return self._document_loader.load_directory(directory)

    def chunk_documents(self, documents: list[SourceDocument]) -> list[SupportDocumentChunk]:
        return self._chunker.chunk_documents(documents)
