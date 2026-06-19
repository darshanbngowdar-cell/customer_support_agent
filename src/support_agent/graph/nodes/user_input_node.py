from support_agent.application.conversation_memory import ConversationMemoryManager
from support_agent.graph.state import SupportAgentState


class UserInputNode:
    """Normalizes user input at the graph boundary."""

    def __init__(self, memory_manager: ConversationMemoryManager) -> None:
        self._memory_manager = memory_manager

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        message = " ".join(state["user_message"].split())
        session_id = state.get("session_id", "default")
        memory = self._memory_manager.initialize(session_id, state.get("memory_state"))
        history = state.get("conversation_history") or self._memory_manager.history_for_prompt(memory)
        return {
            "user_message": message,
            "session_id": session_id,
            "conversation_history": history,
            "memory_state": memory,
            "errors": state.get("errors", []),
        }
