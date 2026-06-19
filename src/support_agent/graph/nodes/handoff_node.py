from support_agent.application.escalation_engine import EscalationEngine
from support_agent.graph.state import SupportAgentState


class HumanHandoffNode:
    """Creates a structured human handoff summary when escalation is required."""

    def __init__(self, escalation_engine: EscalationEngine) -> None:
        self._escalation_engine = escalation_engine

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        decision = state["escalation_decision"]
        if not decision.should_escalate:
            return {}

        return {
            "handoff_summary": self._escalation_engine.build_handoff_summary(
                user_message=state["user_message"],
                conversation_history=state.get("conversation_history", []),
                persona_result=state["persona_result"],
                retrieval_result=state["retrieval_result"],
                decision=decision,
                actions_attempted=[
                    "Persona detection",
                    "Query optimization",
                    "Hybrid retrieval",
                    "Context validation",
                    "Grounded response generation",
                    "Confidence evaluation",
                    "Escalation decision",
                ],
            )
        }
