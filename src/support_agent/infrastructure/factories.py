from support_agent.application.escalation_engine import EscalationEngine
from support_agent.application.conversation_memory import ConversationMemoryManager
from support_agent.config.settings import Settings
from support_agent.domain.escalation import EscalationRuleConfig
from support_agent.infrastructure.embeddings.sentence_transformer_embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from support_agent.infrastructure.loaders.chunker import DynamicDocumentChunker
from support_agent.infrastructure.loaders.document_loader import DocumentLoader
from support_agent.infrastructure.retrievers.bm25 import BM25Retriever
from support_agent.infrastructure.retrievers.fusion import ReciprocalRankFusion
from support_agent.infrastructure.retrievers.hybrid import HybridRetriever
from support_agent.infrastructure.vectorstores.chroma_store import ChromaVectorStore


class RetrievalSystemFactory:
    """Factory for wiring the retrieval system from runtime settings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_document_loader(self) -> DocumentLoader:
        return DocumentLoader()

    def create_chunker(self) -> DynamicDocumentChunker:
        return DynamicDocumentChunker(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
            min_chunk_size=self._settings.min_chunk_size,
            max_chunk_size=self._settings.max_chunk_size,
            small_document_threshold=self._settings.small_document_threshold,
            large_document_threshold=self._settings.large_document_threshold,
        )

    def create_vector_store(self) -> ChromaVectorStore:
        embedding_provider = SentenceTransformerEmbeddingProvider(
            model_name=self._settings.sentence_transformer_model
        )
        return ChromaVectorStore(
            persist_directory=str(self._settings.vector_store_dir),
            collection_name=self._settings.chroma_collection_name,
            embedding_provider=embedding_provider,
        )

    def create_hybrid_retriever(self) -> HybridRetriever:
        vector_store = self.create_vector_store()
        bm25_retriever = BM25Retriever(vector_store.list_chunks())
        fusion = ReciprocalRankFusion(
            rrf_k=self._settings.rrf_k,
            dense_weight=self._settings.dense_weight,
            bm25_weight=self._settings.bm25_weight,
        )
        return HybridRetriever(
            vector_store=vector_store,
            bm25_retriever=bm25_retriever,
            fusion=fusion,
            dense_top_k=self._settings.dense_top_k,
            bm25_top_k=self._settings.bm25_top_k,
            fusion_top_k=self._settings.fusion_top_k,
        )

    def create_escalation_engine(self) -> EscalationEngine:
        return EscalationEngine(
            EscalationRuleConfig(
                retrieval_confidence_threshold=self._settings.retrieval_confidence_threshold,
                overall_confidence_threshold=self._settings.escalation_low_confidence_threshold,
                max_dissatisfaction_signals=self._settings.escalation_max_unresolved_turns,
                billing_keywords=self._settings.csv_tuple(self._settings.escalation_billing_keywords),
                legal_keywords=self._settings.csv_tuple(self._settings.escalation_legal_keywords),
                sensitive_account_keywords=self._settings.csv_tuple(
                    self._settings.escalation_account_keywords
                ),
            )
        )

    def create_memory_manager(self) -> ConversationMemoryManager:
        return ConversationMemoryManager(
            max_turns=self._settings.memory_max_turns,
            token_budget=self._settings.memory_token_budget,
        )
