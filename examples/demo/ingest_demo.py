from pathlib import Path

from support_agent.domain.documents import SourceDocument, SupportDocumentChunk, stable_content_hash, stable_chunk_id
from support_agent.infrastructure.vectorstores.inmemory import InMemoryVectorStore


def load_markdown_files(directory: Path) -> list[SourceDocument]:
    docs = []
    for file in sorted(directory.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        docs.append(SourceDocument(text=text, metadata={"source": str(file)}))
    return docs


def build_chunks_from_documents(documents: list[SourceDocument]) -> list[SupportDocumentChunk]:
    chunks: list[SupportDocumentChunk] = []
    for i, doc in enumerate(documents):
        # naive splitting: whole document as a single chunk for demo
        chunk_id = stable_chunk_id(str(doc.metadata.get("source", f"doc{i}")), doc.text, 0, {})
        chunks.append(
            SupportDocumentChunk(
                chunk_id=chunk_id,
                text=doc.text,
                metadata={"source": doc.metadata.get("source", "demo")},
                content_hash=stable_content_hash(doc.text),
            )
        )
    return chunks


def main() -> None:
    demo_docs = Path(__file__).parent.joinpath("docs")
    documents = load_markdown_files(demo_docs)
    chunks = build_chunks_from_documents(documents)

    store_dir = Path("data/vector_store")
    store_dir.mkdir(parents=True, exist_ok=True)
    persist_path = str(store_dir.joinpath("demo_store.json"))

    store = InMemoryVectorStore(persist_path=persist_path)
    added = store.add_chunks(chunks)
    print(f"Ingested {added} chunks into {persist_path}")


if __name__ == "__main__":
    main()
