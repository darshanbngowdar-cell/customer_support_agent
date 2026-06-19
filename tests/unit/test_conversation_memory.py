from support_agent.application.conversation_memory import ConversationMemoryManager
from support_agent.domain.memory import ConversationMemoryState, ConversationTurn
from support_agent.domain.personas import PersonaDetectionResult, PersonaType
from support_agent.domain.responses import GeneratedSupportResponse


def test_memory_trims_history_to_token_budget() -> None:
    memory = ConversationMemoryState(
        session_id="s1",
        token_budget=200,
        turns=[
            ConversationTurn(
                user_message=f"Question {index} " * 30,
                assistant_response=f"Answer {index} " * 30,
                persona=PersonaType.FRUSTRATED_USER,
                confidence=0.8,
            )
            for index in range(6)
        ],
    )

    history = memory.trimmed_history()

    assert len(history) < 6
    assert "Question 5" in history[-1]


def test_memory_persists_persona_when_detection_uses_fallback() -> None:
    manager = ConversationMemoryManager()
    memory = ConversationMemoryState(
        session_id="s1",
        persisted_persona=PersonaType.TECHNICAL_EXPERT,
    )
    fallback = PersonaDetectionResult(
        persona=PersonaType.FRUSTRATED_USER,
        confidence=0.25,
        matched_indicators=[],
        reasoning="weak evidence",
        used_fallback=True,
    )

    result = manager.persist_persona(fallback, memory)

    assert result.persona == PersonaType.TECHNICAL_EXPERT
    assert result.used_fallback


def test_memory_updates_session_documents_and_turns() -> None:
    manager = ConversationMemoryManager(max_turns=2)
    memory = ConversationMemoryState(session_id="s1")
    response = GeneratedSupportResponse(
        answer="Answer",
        persona=PersonaType.BUSINESS_EXECUTIVE,
        confidence=0.7,
        citations=["sla.md, section Availability"],
        retrieved_chunks=[],
        used_context=True,
    )

    updated = manager.update(memory, "Impact?", response)

    assert updated.persisted_persona == PersonaType.BUSINESS_EXECUTIVE
    assert updated.retrieved_documents == ["sla.md, section Availability"]
    assert updated.turns[0].user_message == "Impact?"
