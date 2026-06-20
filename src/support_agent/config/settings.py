from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="SUPPORT_AGENT_",
    )
    env_prefix: ClassVar[str] = "SUPPORT_AGENT_"

    app_env: str = Field("development", description="Application environment")
    log_level: str = Field("INFO", description="Minimum log verbosity")
    log_format: str = Field("json", description="Log format: json or text")

    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API key for secure LLM calls",
        json_schema_extra={"env": ["OPENAI_API_KEY", "SUPPORT_AGENT_OPENAI_API_KEY"]},
    )
    openai_api_base: str | None = Field(
        default=None,
        description="Custom OpenAI-compatible API base URL.",
        json_schema_extra={"env": ["OPENAI_API_BASE", "SUPPORT_AGENT_OPENAI_BASE"]},
    )
    openai_model: str = Field("gpt-3.5-turbo", description="OpenAI chat model name")
    openai_request_timeout: int = Field(
        30,
        ge=1,
        description="OpenAI request timeout in seconds",
    )
    openai_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for OpenAI generation.",
    )
    openai_max_tokens: int = Field(
        default=512,
        ge=1,
        le=2048,
        description="Maximum tokens for OpenAI generation.",
    )

    data_dir: Path = Field(
        default=Path("data/raw"),
        description="Source document ingestion directory",
    )
    vector_store_dir: Path = Field(
        default=Path("data/vector_store"),
        description="Vector store persistence directory",
    )
    chroma_collection_name: str = Field(
        "support_knowledge_base",
        description="Chroma collection name",
    )

    sentence_transformer_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="Local embedding model name",
    )

    chunk_size: int = Field(
        default=900,
        ge=200,
        description="Maximum chunk size for document ingestion",
    )
    chunk_overlap: int = Field(
        default=150,
        ge=0,
        description="Overlap size between document chunks",
    )
    min_chunk_size: int = Field(
        default=450,
        ge=100,
        description="Minimum chunk size for document ingestion",
    )
    max_chunk_size: int = Field(
        default=1400,
        ge=300,
        description="Maximum chunk size when splitting large documents",
    )
    small_document_threshold: int = Field(
        default=1800,
        ge=500,
        description="Document length threshold that uses smaller chunking",
    )
    large_document_threshold: int = Field(
        default=9000,
        ge=1000,
        description="Document length threshold that uses larger chunking",
    )

    retrieval_top_k: int = Field(
        default=4,
        ge=1,
        description="Number of top retrieval hits to preserve for fusion",
    )
    dense_top_k: int = Field(
        default=8,
        ge=1,
        description="Dense retriever top-k result size",
    )
    bm25_top_k: int = Field(
        default=8,
        ge=1,
        description="BM25 retriever top-k result size",
    )
    fusion_top_k: int = Field(
        default=4,
        ge=1,
        description="Reciprocal rank fusion result size",
    )
    rrf_k: int = Field(
        default=60,
        ge=1,
        description="Reciprocal rank fusion parameter",
    )
    dense_weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Dense retrieval weight",
    )
    bm25_weight: float = Field(
        default=1.0,
        ge=0.0,
        description="BM25 retrieval weight",
    )
    retrieval_confidence_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Minimum retrieval confidence required for grounded answers",
    )

    escalation_low_confidence_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Escalation threshold for low confidence",
    )
    escalation_max_unresolved_turns: int = Field(
        default=2,
        ge=1,
        description="Maximum unresolved turn count before escalation",
    )
    escalation_billing_keywords: str = Field(
        default="billing,invoice,refund,charge,payment,subscription",
        description="Comma-separated billing escalation signals",
    )
    escalation_legal_keywords: str = Field(
        default="legal,lawsuit,compliance,contract,liability,terms of service,gdpr",
        description="Comma-separated legal escalation signals",
    )
    escalation_account_keywords: str = Field(
        default=(
            "account deletion,delete my account,security breach,compromised,hacked,"
            "2fa,mfa,personal data"
        ),
        description="Comma-separated account escalation signals",
    )
    memory_max_turns: int = Field(
        default=12,
        ge=1,
        description="Maximum number of conversation turns to keep in memory",
    )
    memory_token_budget: int = Field(
        default=1600,
        ge=200,
        description="Approximate token budget for conversation memory",
    )

    cache_enabled: bool = Field(
        default=True,
        description="Enable in-memory response caching for repeated prompts",
    )
    cache_ttl_seconds: int = Field(
        default=300,
        ge=10,
        description="Time-to-live for cached responses in seconds",
    )
    cache_max_items: int = Field(
        default=256,
        ge=16,
        description="Maximum number of cached responses to keep",
    )

    rate_limit_max_requests: int = Field(
        default=10,
        ge=1,
        description="Maximum requests per session in a rate limit window",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        description="Rate limit window duration in seconds",
    )

    health_check_timeout_seconds: int = Field(
        default=10,
        ge=1,
        description="Timeout for health checks in seconds",
    )

    def csv_tuple(self, value: str) -> tuple[str, ...]:
        return tuple(item.strip().lower() for item in value.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
