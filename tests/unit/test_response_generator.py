from support_agent.application.response_generator import ResponseGenerator
from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk, SupportDocumentChunk
from support_agent.domain.personas import PersonaDetectionResult, PersonaType
from support_agent.infrastructure.llm.mock_client import MockLLMClient
from support_agent.prompts.response_prompts import build_response_generation_prompt


def _persona(persona: PersonaType) -> PersonaDetectionResult:
    return PersonaDetectionResult(
        persona=persona,
        confidence=0.9,
        matched_indicators=["api"],
        reasoning="test",
    )


def _retrieved(score: float = 0.7) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=SupportDocumentChunk(
            chunk_id="chunk-1",
            text="Users can reset passwords from Settings > Security. Reset links expire in 15 minutes.",
            metadata={"source": "password_reset_guide.pdf", "page_number": 2},
            content_hash="hash-1",
        ),
        score=score,
        retrieval_method="hybrid_rrf",
    )


def test_generates_grounded_response_with_citations() -> None:
    llm = MockLLMClient("Follow the password reset steps from the documentation.")
    generator = ResponseGenerator(llm_client=llm, minimum_retrieval_confidence=0.35)

    result = generator.generate(
        question="How do I reset my password?",
        persona_result=_persona(PersonaType.FRUSTRATED_USER),
        retrieval_result=HybridRetrievalResult(results=[_retrieved()]),
    )

    assert result.used_context
    assert not result.requires_escalation
    assert result.citations == ["password_reset_guide.pdf, page 2"]
    assert "Sources: password_reset_guide.pdf, page 2" in result.answer
    assert result.confidence > 0.35


def test_refuses_to_answer_without_retrieved_context() -> None:
    generator = ResponseGenerator(MockLLMClient())

    result = generator.generate(
        question="What is your undocumented retention policy?",
        persona_result=_persona(PersonaType.BUSINESS_EXECUTIVE),
        retrieval_result=HybridRetrievalResult(results=[]),
    )

    assert not result.used_context
    assert result.requires_escalation
    assert result.citations == []
    assert "do not have enough support documentation" in result.answer


def test_refuses_low_confidence_context() -> None:
    generator = ResponseGenerator(MockLLMClient(), minimum_retrieval_confidence=0.8)

    result = generator.generate(
        question="How do I reset my password?",
        persona_result=_persona(PersonaType.TECHNICAL_EXPERT),
        retrieval_result=HybridRetrievalResult(results=[_retrieved(score=0.2)]),
    )

    assert result.requires_escalation
    assert result.escalation_reason is not None
    assert not result.used_context


def test_prompt_template_changes_by_persona() -> None:
    tech_prompt = build_response_generation_prompt(
        question="Why did API auth fail?",
        persona=PersonaType.TECHNICAL_EXPERT,
        chunks=[_retrieved()],
    )[1]
    exec_prompt = build_response_generation_prompt(
        question="What is the impact?",
        persona=PersonaType.BUSINESS_EXECUTIVE,
        chunks=[_retrieved()],
    )[1]

    assert "Root cause" in tech_prompt or "root cause" in tech_prompt
    assert "business impact" in exec_prompt
    assert "password_reset_guide.pdf, page 2" in tech_prompt


def test_duplicate_chunks_are_not_sent_to_llm() -> None:
    duplicate = _retrieved()
    llm = MockLLMClient("Use the cited reset guidance.")
    generator = ResponseGenerator(llm)

    result = generator.generate(
        question="Password reset?",
        persona_result=_persona(PersonaType.FRUSTRATED_USER),
        retrieval_result=HybridRetrievalResult(results=[duplicate, duplicate]),
    )

    assert len(result.retrieved_chunks) == 1
    assert len(llm.calls) == 1
