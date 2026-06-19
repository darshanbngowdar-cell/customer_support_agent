from enum import StrEnum

from pydantic import BaseModel, Field


class PersonaType(StrEnum):
    """Supported customer personas."""

    TECHNICAL_EXPERT = "Technical Expert"
    FRUSTRATED_USER = "Frustrated User"
    BUSINESS_EXECUTIVE = "Business Executive"


class PersonaDefinition(BaseModel):
    """Configurable definition used by prompt and rule-based classification."""

    persona: PersonaType
    description: str
    response_style: list[str]
    positive_indicators: list[str] = Field(default_factory=list)
    negative_indicators: list[str] = Field(default_factory=list)
    priority: int = 0


class PersonaDetectionResult(BaseModel):
    """Classifier output with confidence and explainability fields."""

    persona: PersonaType
    confidence: float = Field(ge=0.0, le=1.0)
    matched_indicators: list[str] = Field(default_factory=list)
    reasoning: str
    used_fallback: bool = False


DEFAULT_PERSONA_DEFINITIONS: tuple[PersonaDefinition, ...] = (
    PersonaDefinition(
        persona=PersonaType.TECHNICAL_EXPERT,
        description=(
            "Uses technical terminology, asks for logs, API details, configurations, "
            "root cause, or debugging steps."
        ),
        response_style=[
            "Detailed",
            "Technical",
            "Root-cause oriented",
            "Step-by-step troubleshooting",
        ],
        positive_indicators=[
            "api",
            "authentication",
            "auth",
            "logs",
            "stack trace",
            "configuration",
            "config",
            "webhook",
            "endpoint",
            "payload",
            "http",
            "status code",
            "error code",
            "sdk",
            "database",
            "latency",
            "timeout",
            "root cause",
            "debug",
        ],
        priority=2,
    ),
    PersonaDefinition(
        persona=PersonaType.FRUSTRATED_USER,
        description=(
            "Uses emotional language, repeated complaints, urgency, dissatisfaction, "
            "or asks for immediate help."
        ),
        response_style=[
            "Empathetic",
            "Simple",
            "Reassuring",
            "Action-oriented",
        ],
        positive_indicators=[
            "angry",
            "frustrated",
            "annoyed",
            "nothing works",
            "tried everything",
            "again",
            "still not working",
            "urgent",
            "asap",
            "unacceptable",
            "terrible",
            "hate",
            "fed up",
            "wasting my time",
            "!",
        ],
        priority=3,
    ),
    PersonaDefinition(
        persona=PersonaType.BUSINESS_EXECUTIVE,
        description=(
            "Outcome-focused, interested in business impact, timelines, operational "
            "risk, customer impact, and concise resolution guidance."
        ),
        response_style=[
            "Concise",
            "Impact-focused",
            "Minimal technical jargon",
            "Resolution-time oriented",
        ],
        positive_indicators=[
            "business impact",
            "impact",
            "operations",
            "revenue",
            "sla",
            "timeline",
            "eta",
            "when will",
            "customer impact",
            "executive",
            "risk",
            "priority",
            "status update",
            "summary",
            "resolution",
        ],
        priority=1,
    ),
)
