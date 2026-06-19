from support_agent.application.retrieval_service import RetrievalService
from support_agent.graph.state import SupportAgentState


class HybridRetrievalNode:
    """Runs hybrid retrieval for the optimized query."""

    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval_service = retrieval_service

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        query = state.get("optimized_query") or state["user_message"]
        return {"retrieval_result": self._retrieval_service.retrieve(query)}
