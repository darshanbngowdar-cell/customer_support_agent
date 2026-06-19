from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from support_agent.domain.personas import PersonaType


class HumanHandoffSummary(BaseModel):
    """Structured summary for a human support representative."""

    persona: PersonaType
    issue_summary: str
    conversation_history: list[str] = Field(default_factory=list)
    retrieved_documents: list[str] = Field(default_factory=list)
    attempted_steps: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    recommendation: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    escalation_reasons: list[str] = Field(default_factory=list)

    @property
    def issue(self) -> str:
        return self.issue_summary

    @property
    def documents_used(self) -> list[str]:
        return self.retrieved_documents

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
