import time

from support_agent.application.response_generator import ResponseGenerator
from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk, SupportDocumentChunk
from support_agent.domain.personas import PersonaDetectionResult, PersonaType
from support_agent.infrastructure.llm.mock_client import MockLLMClient


def _persona() -> PersonaDetectionResult:
    return PersonaDetectionResult(
        persona=PersonaType.TECHNICAL_EXPERT,
        confidence=0.9,
        matched_indicators=["api"],
        reasoning="test",
    )


def _chunk(text: str, cid: str, score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=SupportDocumentChunk(
            chunk_id=cid,
            text=text,
            metadata={"source": "doc.md"},
            content_hash="h",
        ),
        score=score,
        retrieval_method="dense",
    )


def test_retrieval_confidence_increases_with_more_supporting_chunks() -> None:
    llm = MockLLMClient("ok")
    gen = ResponseGenerator(llm_client=llm)

    # Single chunk
    r1 = gen._retrieval_confidence([_chunk("a", "c1", score=0.4)])
    # Four supporting chunks should increase supporting evidence up to 0.1
    chunks = [_chunk("a", f"c{i}", score=0.4) for i in range(4)]
    r2 = gen._retrieval_confidence(chunks)

    assert r2 >= r1
    assert r2 - r1 > 0


def test_ensure_citations_does_not_duplicate_existing() -> None:
    # LLM returns an answer that already includes the citation string
    llm = MockLLMClient("Refer to doc.md in the docs. Sources: doc.md")
    gen = ResponseGenerator(llm_client=llm)

    chunk = _chunk("some text", "c1", score=0.8)
    res = gen.generate(
        question="q",
        persona_result=_persona(),
        retrieval_result=HybridRetrievalResult(results=[chunk]),
    )

    # The answer should not have duplicated "Sources: doc.md"
    assert res.answer.count("Sources: doc.md") == 1


def test_response_generator_cache_ttl_eviction() -> None:
    llm = MockLLMClient("first")
    gen = ResponseGenerator(llm_client=llm, cache_enabled=True, cache_ttl_seconds=1, cache_max_items=10)

    chunk = _chunk("text", "c1", score=0.9)
    p = _persona()

    r1 = gen.generate(question="q", persona_result=p, retrieval_result=HybridRetrievalResult(results=[chunk]))
    # Immediate second call should use cache
    r2 = gen.generate(question="q", persona_result=p, retrieval_result=HybridRetrievalResult(results=[chunk]))
    assert len(llm.calls) == 1

    # Wait for TTL to expire
    time.sleep(1.1)
    r3 = gen.generate(question="q", persona_result=p, retrieval_result=HybridRetrievalResult(results=[chunk]))
    assert len(llm.calls) == 2
