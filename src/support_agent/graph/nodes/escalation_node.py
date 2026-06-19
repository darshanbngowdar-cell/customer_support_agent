from support_agent.application.escalation_engine import EscalationEngine
from support_agent.graph.state import SupportAgentState


class EscalationDecisionNode:
    """Decides whether a conversation needs human support."""

    def __init__(self, escalation_engine: EscalationEngine) -> None:
        self._escalation_engine = escalation_engine

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        decision = self._escalation_engine.evaluate(
            user_message=state["user_message"],
            conversation_history=state.get("conversation_history", []),
            persona_result=state["persona_result"],
            retrieval_result=state["retrieval_result"],
            generated_response=state["generated_response"],
            overall_confidence=state.get("confidence_score", state["generated_response"].confidence),
            context_validation_reasons=state.get("context_validation_reasons", []),
        )
        return {
            "escalation_decision": decision,
        }
