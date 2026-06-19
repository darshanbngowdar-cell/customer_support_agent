from support_agent.domain.responses import GeneratedSupportResponse
from support_agent.application.conversation_memory import ConversationMemoryManager
from support_agent.graph.state import SupportAgentState


class FinalResponseNode:
    """Prepares the final response object for callers."""

    def __init__(self, memory_manager: ConversationMemoryManager) -> None:
        self._memory_manager = memory_manager

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        response = state["generated_response"]
        decision = state["escalation_decision"]
        final_response = GeneratedSupportResponse(
            answer=response.answer,
            persona=response.persona,
            confidence=state.get("confidence_score", response.confidence),
            citations=response.citations,
            retrieved_chunks=response.retrieved_chunks,
            used_context=response.used_context,
            requires_escalation=decision.should_escalate,
            escalation_reason="; ".join(decision.reasons) if decision.reasons else None,
        )
        memory = self._memory_manager.update(
            memory=state["memory_state"],
            user_message=state["user_message"],
            response=final_response,
        )
        return {"final_response": final_response, "memory_state": memory}
