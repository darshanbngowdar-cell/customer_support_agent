from typing import Any, NotRequired, TypedDict

from support_agent.domain.documents import HybridRetrievalResult
from support_agent.domain.escalation import EscalationDecision
from support_agent.domain.handoff import HumanHandoffSummary
from support_agent.domain.memory import ConversationMemoryState
from support_agent.domain.personas import PersonaDetectionResult
from support_agent.domain.responses import GeneratedSupportResponse


class SupportAgentState(TypedDict):
    """LangGraph state shared by all support-agent workflow nodes."""

    user_message: str
    session_id: NotRequired[str]
    conversation_history: list[str]
    memory_state: NotRequired[ConversationMemoryState]
    optimized_query: NotRequired[str]
    persona_result: NotRequired[PersonaDetectionResult]
    retrieval_result: NotRequired[HybridRetrievalResult]
    context_is_valid: NotRequired[bool]
    context_validation_reasons: NotRequired[list[str]]
    generated_response: NotRequired[GeneratedSupportResponse]
    confidence_score: NotRequired[float]
    confidence_reasons: NotRequired[list[str]]
    escalation_decision: NotRequired[EscalationDecision]
    handoff_summary: NotRequired[HumanHandoffSummary]
    final_response: NotRequired[GeneratedSupportResponse]
    errors: NotRequired[list[str]]
    metadata: NotRequired[dict[str, Any]]
