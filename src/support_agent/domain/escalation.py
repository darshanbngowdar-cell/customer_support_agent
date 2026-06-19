from enum import StrEnum

from pydantic import BaseModel, Field


class EscalationTrigger(StrEnum):
    """Supported escalation trigger categories."""

    LOW_RETRIEVAL_CONFIDENCE = "low_retrieval_confidence"
    NO_RELEVANT_DOCUMENTS = "no_relevant_documents"
    REPEATED_DISSATISFACTION = "repeated_dissatisfaction"
    BILLING_ISSUE = "billing_issue"
    LEGAL_ISSUE = "legal_issue"
    SENSITIVE_ACCOUNT_ISSUE = "sensitive_account_issue"
    UNKNOWN_REQUEST = "unknown_request"
    RESPONSE_REQUIRES_ESCALATION = "response_requires_escalation"


class EscalationRuleConfig(BaseModel):
    """Configurable thresholds and keyword rules for escalation."""

    retrieval_confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    overall_confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    max_dissatisfaction_signals: int = Field(default=2, ge=1)
    billing_keywords: tuple[str, ...] = (
        "billing",
        "invoice",
        "refund",
        "charge",
        "charged",
        "payment",
        "subscription",
    )
    legal_keywords: tuple[str, ...] = (
        "legal",
        "lawsuit",
        "compliance",
        "contract",
        "liability",
        "terms of service",
        "gdpr",
        "data processing agreement",
    )
    sensitive_account_keywords: tuple[str, ...] = (
        "account deletion",
        "delete my account",
        "security breach",
        "compromised",
        "hacked",
        "password exposed",
        "2fa",
        "mfa",
        "personal data",
        "bank account",
    )
    dissatisfaction_keywords: tuple[str, ...] = (
        "still not working",
        "tried everything",
        "not resolved",
        "again",
        "angry",
        "frustrated",
        "unacceptable",
        "wasting my time",
        "nothing works",
    )
    unknown_request_keywords: tuple[str, ...] = (
        "undocumented",
        "not listed",
        "unknown",
        "something else",
        "not covered",
    )


class EscalationDecision(BaseModel):
    """Decision produced by the escalation node."""

    should_escalate: bool
    reasons: list[str] = Field(default_factory=list)
    triggers: list[EscalationTrigger] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
