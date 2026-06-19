from support_agent.domain.memory import ConversationMemoryState, ConversationTurn
from support_agent.domain.personas import PersonaDetectionResult
from support_agent.domain.responses import GeneratedSupportResponse


class ConversationMemoryManager:
    """Maintains session memory with lightweight token-aware trimming."""

    def __init__(self, max_turns: int = 12, token_budget: int = 1600) -> None:
        self._max_turns = max_turns
        self._token_budget = token_budget

    def initialize(
        self,
        session_id: str,
        existing_memory: ConversationMemoryState | None,
    ) -> ConversationMemoryState:
        if existing_memory is not None:
            return existing_memory
        return ConversationMemoryState(session_id=session_id, token_budget=self._token_budget)

    def history_for_prompt(self, memory: ConversationMemoryState) -> list[str]:
        return memory.trimmed_history()

    def persist_persona(
        self,
        detection: PersonaDetectionResult,
        memory: ConversationMemoryState,
    ) -> PersonaDetectionResult:
        if detection.used_fallback and memory.persisted_persona is not None:
            return PersonaDetectionResult(
                persona=memory.persisted_persona,
                confidence=max(detection.confidence, 0.4),
                matched_indicators=detection.matched_indicators,
                reasoning=(
                    f"{detection.reasoning} Reused persisted session persona: "
                    f"{memory.persisted_persona.value}."
                ),
                used_fallback=True,
            )
        return detection

    def update(
        self,
        memory: ConversationMemoryState,
        user_message: str,
        response: GeneratedSupportResponse,
    ) -> ConversationMemoryState:
        turn = ConversationTurn(
            user_message=user_message,
            assistant_response=response.answer,
            persona=response.persona,
            retrieved_documents=response.citations,
            confidence=response.confidence,
        )
        return memory.append_turn(turn, max_turns=self._max_turns)
