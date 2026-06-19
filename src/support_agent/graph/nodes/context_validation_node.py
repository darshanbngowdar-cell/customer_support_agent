from support_agent.graph.state import SupportAgentState


class ContextValidationNode:
    """Validates whether retrieved context is usable for grounded generation."""

    def __init__(self, minimum_score: float = 0.35) -> None:
        self._minimum_score = minimum_score

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        retrieval_result = state["retrieval_result"]
        reasons: list[str] = []

        if not retrieval_result.results:
            reasons.append("No retrieved chunks were returned.")

        best_score = max((result.score for result in retrieval_result.results), default=0.0)
        if best_score < self._minimum_score:
            reasons.append("Best retrieval score is below the context validation threshold.")

        return {
            "context_is_valid": not reasons,
            "context_validation_reasons": reasons,
        }
