from langchain_text_splitters import RecursiveCharacterTextSplitter

from support_agent.domain.documents import (
    SourceDocument,
    SupportDocumentChunk,
    stable_chunk_id,
    stable_content_hash,
)


class DynamicDocumentChunker:
    """Chunks documents with size adjusted to each document's length."""

    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        min_chunk_size: int,
        max_chunk_size: int,
        small_document_threshold: int,
        large_document_threshold: int,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._min_chunk_size = min_chunk_size
        self._max_chunk_size = max_chunk_size
        self._small_document_threshold = small_document_threshold
        self._large_document_threshold = large_document_threshold

    def chunk_documents(self, documents: list[SourceDocument]) -> list[SupportDocumentChunk]:
        chunks: list[SupportDocumentChunk] = []
        seen_hashes: set[str] = set()

        for document in documents:
            splitter = self._splitter_for(document.text)
            split_texts = splitter.split_text(document.text)
            for chunk_index, text in enumerate(split_texts):
                clean_text = text.strip()
                if not clean_text:
                    continue
                content_hash = stable_content_hash(clean_text)
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)

                metadata = {
                    **document.metadata,
                    "chunk_index": chunk_index,
                    "chunk_size": splitter._chunk_size,
                    "chunk_overlap": splitter._chunk_overlap,
                }
                source = str(metadata.get("source", "unknown"))
                chunks.append(
                    SupportDocumentChunk(
                        chunk_id=stable_chunk_id(source, clean_text, chunk_index, metadata),
                        text=clean_text,
                        metadata=metadata,
                        content_hash=content_hash,
                    )
                )
        return chunks

    def _splitter_for(self, text: str) -> RecursiveCharacterTextSplitter:
        selected_chunk_size = self._select_chunk_size(len(text))
        selected_overlap = min(self._chunk_overlap, selected_chunk_size // 4)
        return RecursiveCharacterTextSplitter(
            chunk_size=selected_chunk_size,
            chunk_overlap=selected_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _select_chunk_size(self, text_length: int) -> int:
        if text_length <= self._small_document_threshold:
            return self._min_chunk_size
        if text_length >= self._large_document_threshold:
            return self._max_chunk_size
        return self._chunk_size
