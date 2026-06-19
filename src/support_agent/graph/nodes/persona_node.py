from support_agent.application.conversation_memory import ConversationMemoryManager
from support_agent.application.persona_detector import PersonaDetector
from support_agent.graph.state import SupportAgentState


class PersonaDetectionNode:
    """Detects the customer's support persona."""

    def __init__(self, detector: PersonaDetector, memory_manager: ConversationMemoryManager) -> None:
        self._detector = detector
        self._memory_manager = memory_manager

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        result = self._detector.detect(
            message=state["user_message"],
            conversation_history=state.get("conversation_history", []),
        )
        result = self._memory_manager.persist_persona(result, state["memory_state"])
        return {"persona_result": result}
