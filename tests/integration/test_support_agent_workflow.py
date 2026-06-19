from support_agent.application.persona_detector import PersonaDetector
from support_agent.application.response_generator import ResponseGenerator
from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk, SupportDocumentChunk
from support_agent.graph.dependencies import GraphRetryConfig, SupportGraphDependencies
from support_agent.graph.workflow import SupportAgentWorkflow
from support_agent.infrastructure.llm.mock_client import MockLLMClient


class SuccessfulRetrievalService:
    def __init__(self) -> None:
        self.calls = 0

    def retrieve(self, query: str) -> HybridRetrievalResult:
        self.calls += 1
        return HybridRetrievalResult(
            results=[
                RetrievedChunk(
                    chunk=SupportDocumentChunk(
                        chunk_id="api-auth-1",
                        text="API authentication returns 401 when credentials are invalid.",
                        metadata={"source": "api_authentication.md", "section_name": "Authentication"},
                        content_hash="hash-api-auth-1",
                    ),
                    score=0.8,
                    retrieval_method="hybrid_rrf",
                )
            ]
        )


class EmptyRetrievalService:
    def retrieve(self, query: str) -> HybridRetrievalResult:
        return HybridRetrievalResult(results=[])


class FlakyRetrievalService(SuccessfulRetrievalService):
    def retrieve(self, query: str) -> HybridRetrievalResult:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary vector store failure")
        return HybridRetrievalResult(
            results=[
                RetrievedChunk(
                    chunk=SupportDocumentChunk(
                        chunk_id="retry-1",
                        text="Password reset links expire in 15 minutes.",
                        metadata={"source": "password_reset_guide.pdf", "page_number": 2},
                        content_hash="hash-retry-1",
                    ),
                    score=0.8,
                    retrieval_method="hybrid_rrf",
                )
            ]
        )


def _workflow(retrieval_service: object):
    dependencies = SupportGraphDependencies(
        persona_detector=PersonaDetector(),
        retrieval_service=retrieval_service,
        response_generator=ResponseGenerator(MockLLMClient("Use the cited support guidance.")),
        retry_config=GraphRetryConfig(max_attempts=2),
    )
    return SupportAgentWorkflow(dependencies).compile(use_memory=False)


def test_workflow_returns_final_response_without_escalation() -> None:
    graph = _workflow(SuccessfulRetrievalService())

    state = graph.invoke(
        {
            "user_message": "Can you explain the API authentication error logs?",
            "conversation_history": [],
        }
    )

    assert state["final_response"].persona.value == "Technical Expert"
    assert not state["final_response"].requires_escalation
    assert state["final_response"].citations == ["api_authentication.md, section Authentication"]


def test_workflow_creates_handoff_when_context_is_missing() -> None:
    graph = _workflow(EmptyRetrievalService())

    state = graph.invoke(
        {
            "user_message": "What is your undocumented legal policy?",
            "conversation_history": [],
        }
    )

    assert state["final_response"].requires_escalation
    assert state["handoff_summary"].issue == "What is your undocumented legal policy?"
    assert "Hybrid retrieval" in state["handoff_summary"].attempted_steps


def test_workflow_retries_recoverable_retrieval_failure() -> None:
    retrieval_service = FlakyRetrievalService()
    graph = _workflow(retrieval_service)

    state = graph.invoke(
        {
            "user_message": "I tried everything and password reset still is not working!",
            "conversation_history": [],
        }
    )

    assert retrieval_service.calls == 2
    assert state["final_response"].citations == ["password_reset_guide.pdf, page 2"]


def test_workflow_persists_memory_across_session_turns() -> None:
    retrieval_service = SuccessfulRetrievalService()
    dependencies = SupportGraphDependencies(
        persona_detector=PersonaDetector(),
        retrieval_service=retrieval_service,
        response_generator=ResponseGenerator(MockLLMClient("Use the cited support guidance.")),
        retry_config=GraphRetryConfig(max_attempts=2),
    )
    graph = SupportAgentWorkflow(dependencies).compile(use_memory=True)
    config = {"configurable": {"thread_id": "session-1"}}

    first = graph.invoke(
        {
            "session_id": "session-1",
            "user_message": "Can you explain the API authentication error logs?",
            "conversation_history": [],
        },
        config=config,
    )
    second = graph.invoke(
        {
            "session_id": "session-1",
            "user_message": "What about the same issue?",
            "conversation_history": [],
        },
        config=config,
    )

    assert len(first["memory_state"].turns) == 1
    assert len(second["memory_state"].turns) == 2
    assert second["memory_state"].persisted_persona.value == "Technical Expert"
    assert retrieval_service.calls == 2
