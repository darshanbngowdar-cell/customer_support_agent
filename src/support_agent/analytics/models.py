from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class AnalyticsRunRecord(BaseModel):
    """Snapshot of metrics captured from a single support-agent workflow run."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float = Field(ge=0.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    persona: str
    persona_confidence: float = Field(ge=0.0, le=1.0)
    retrieval_scores: list[float] = Field(default_factory=list)
    retrieved_documents: list[str] = Field(default_factory=list)
    escalated: bool = False
    conversation_turn_count: int = Field(default=0, ge=0)
    context_is_valid: bool = True


class ConversationStatistics(BaseModel):
    """Aggregated conversation metrics across recorded runs."""

    total_runs: int = 0
    unique_sessions: int = 0
    total_turns: int = 0
    average_turns_per_session: float = 0.0
    average_confidence: float = 0.0
    escalation_rate: float = 0.0


class AnalyticsSummary(BaseModel):
    """Dashboard-ready aggregates derived from run records."""

    records: list[AnalyticsRunRecord] = Field(default_factory=list)
    average_latency_ms: float = 0.0
    average_confidence: float = 0.0
    escalation_count: int = 0
    persona_counts: dict[str, int] = Field(default_factory=dict)
    document_retrieval_counts: dict[str, int] = Field(default_factory=dict)
    conversation_stats: ConversationStatistics = Field(default_factory=ConversationStatistics)
