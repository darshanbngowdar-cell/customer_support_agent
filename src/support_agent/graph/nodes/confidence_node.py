from support_agent.graph.state import SupportAgentState


class ConfidenceEvaluationNode:
    """Evaluates end-to-end confidence from persona, retrieval, context, and response."""

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        reasons: list[str] = []
        persona_confidence = state["persona_result"].confidence
        response_confidence = state["generated_response"].confidence
        context_is_valid = state.get("context_is_valid", False)

        score = min(persona_confidence, response_confidence)
        if not context_is_valid:
            score = min(score, 0.2)
            reasons.extend(state.get("context_validation_reasons", []))
        if state["generated_response"].requires_escalation:
            score = min(score, 0.2)
            if state["generated_response"].escalation_reason:
                reasons.append(state["generated_response"].escalation_reason)

        return {
            "confidence_score": round(score, 3),
            "confidence_reasons": reasons,
        }
