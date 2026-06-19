from datetime import UTC, datetime

from pydantic import BaseModel, Field

from support_agent.domain.personas import PersonaType


class ConversationTurn(BaseModel):
    """One completed user-assistant exchange."""

    user_message: str
    assistant_response: str
    persona: PersonaType
    retrieved_documents: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def compact_text(self) -> str:
        docs = ", ".join(self.retrieved_documents) or "none"
        return (
            f"User: {self.user_message}\n"
            f"Assistant: {self.assistant_response}\n"
            f"Persona: {self.persona.value}; Sources: {docs}; Confidence: {self.confidence:.2f}"
        )


class ConversationMemoryState(BaseModel):
    """Session-level memory persisted through LangGraph checkpoints."""

    session_id: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    persisted_persona: PersonaType | None = None
    retrieved_documents: list[str] = Field(default_factory=list)
    token_budget: int = Field(default=1600, ge=200)

    def trimmed_history(self) -> list[str]:
        selected: list[str] = []
        estimated_tokens = 0
        for turn in reversed(self.turns):
            text = turn.compact_text()
            turn_tokens = estimate_tokens(text)
            if selected and estimated_tokens + turn_tokens > self.token_budget:
                break
            selected.append(text)
            estimated_tokens += turn_tokens
        return list(reversed(selected))

    def recent_documents(self, limit: int = 5) -> list[str]:
        seen: set[str] = set()
        documents: list[str] = []
        for document in reversed(self.retrieved_documents):
            if document in seen:
                continue
            seen.add(document)
            documents.append(document)
            if len(documents) >= limit:
                break
        return list(reversed(documents))

    def append_turn(self, turn: ConversationTurn, max_turns: int) -> "ConversationMemoryState":
        documents = [*self.retrieved_documents, *turn.retrieved_documents]
        return ConversationMemoryState(
            session_id=self.session_id,
            turns=[*self.turns, turn][-max_turns:],
            persisted_persona=turn.persona,
            retrieved_documents=documents[-max_turns * 5 :],
            token_budget=self.token_budget,
        )


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
