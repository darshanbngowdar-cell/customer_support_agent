from typing import Any

from support_agent.domain.responses import GeneratedSupportResponse
from support_agent.graph.state import SupportAgentState


class SupportAgentService:
    """Application boundary for running the LangGraph support workflow."""

    def __init__(self, compiled_graph: Any) -> None:
        self._compiled_graph = compiled_graph

    def handle_message(
        self,
        message: str,
        session_id: str = "default",
        conversation_history: list[str] | None = None,
    ) -> GeneratedSupportResponse:
        initial_state: SupportAgentState = {
            "user_message": message,
            "session_id": session_id,
            "conversation_history": conversation_history or [],
        }
        final_state = self._compiled_graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
        )
        return final_state["final_response"]

    def run(
        self,
        message: str,
        session_id: str = "default",
        conversation_history: list[str] | None = None,
    ) -> SupportAgentState:
        initial_state: SupportAgentState = {
            "user_message": message,
            "session_id": session_id,
            "conversation_history": conversation_history or [],
        }
        return self._compiled_graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
        )
