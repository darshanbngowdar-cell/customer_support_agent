from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    data_dir: Path = Path("data/raw")
    vector_store_dir: Path = Path("data/vector_store")
    chroma_collection_name: str = "support_knowledge_base"

    sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = Field(default=900, ge=200)
    chunk_overlap: int = Field(default=150, ge=0)
    min_chunk_size: int = Field(default=450, ge=100)
    max_chunk_size: int = Field(default=1400, ge=300)
    small_document_threshold: int = Field(default=1800, ge=500)
    large_document_threshold: int = Field(default=9000, ge=1000)

    retrieval_top_k: int = Field(default=4, ge=1)
    dense_top_k: int = Field(default=8, ge=1)
    bm25_top_k: int = Field(default=8, ge=1)
    fusion_top_k: int = Field(default=4, ge=1)
    rrf_k: int = Field(default=60, ge=1)
    dense_weight: float = Field(default=1.0, ge=0.0)
    bm25_weight: float = Field(default=1.0, ge=0.0)
    retrieval_confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)

    escalation_low_confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    escalation_max_unresolved_turns: int = Field(default=2, ge=1)
    escalation_billing_keywords: str = "billing,invoice,refund,charge,payment,subscription"
    escalation_legal_keywords: str = "legal,lawsuit,compliance,contract,liability,terms of service,gdpr"
    escalation_account_keywords: str = (
        "account deletion,delete my account,security breach,compromised,hacked,2fa,mfa,personal data"
    )
    memory_max_turns: int = Field(default=12, ge=1)
    memory_token_budget: int = Field(default=1600, ge=200)

    def csv_tuple(self, value: str) -> tuple[str, ...]:
        return tuple(item.strip().lower() for item in value.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
