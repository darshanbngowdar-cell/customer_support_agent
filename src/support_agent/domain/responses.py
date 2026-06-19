from pydantic import BaseModel, Field

from support_agent.domain.documents import RetrievedChunk
from support_agent.domain.personas import PersonaType


class GeneratedSupportResponse(BaseModel):
    """Grounded support response returned by the response-generation component."""

    answer: str
    persona: PersonaType
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[str] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    used_context: bool
    requires_escalation: bool = False
    escalation_reason: str | None = None
