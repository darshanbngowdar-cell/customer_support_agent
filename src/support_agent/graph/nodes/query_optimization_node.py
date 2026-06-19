from support_agent.graph.state import SupportAgentState


class QueryOptimizationNode:
    """Creates a retrieval-friendly query from the message and detected persona."""

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        persona_result = state["persona_result"]
        memory = state.get("memory_state")
        history_tail = " ".join(state.get("conversation_history", [])[-2:])
        recent_documents = " ".join(memory.recent_documents() if memory is not None else [])
        follow_up_context = recent_documents if self._looks_like_follow_up(state["user_message"]) else ""
        optimized_query = " ".join(
            part
            for part in [
                state["user_message"],
                history_tail,
                follow_up_context,
                persona_result.persona.value,
                " ".join(persona_result.matched_indicators),
            ]
            if part
        )
        return {"optimized_query": optimized_query}

    @staticmethod
    def _looks_like_follow_up(message: str) -> bool:
        normalized = message.lower().strip()
        follow_up_markers = (
            "what about",
            "how about",
            "that",
            "those",
            "it",
            "same issue",
            "still",
            "then",
            "next",
        )
        return len(normalized.split()) <= 12 or any(marker in normalized for marker in follow_up_markers)
