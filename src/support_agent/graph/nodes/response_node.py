from support_agent.application.response_generator import ResponseGenerator
from support_agent.graph.state import SupportAgentState

__all__ = ["ResponseGenerator"]


class ResponseGenerationNode:
    """Generates a persona-adaptive grounded response."""

    def __init__(self, response_generator: ResponseGenerator) -> None:
        self._response_generator = response_generator

    def __call__(self, state: SupportAgentState) -> dict[str, object]:
        response = self._response_generator.generate(
            question=state["user_message"],
            persona_result=state["persona_result"],
            retrieval_result=state["retrieval_result"],
        )
        return {"generated_response": response}
