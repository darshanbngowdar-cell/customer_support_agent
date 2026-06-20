from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk
from support_agent.domain.personas import PersonaDetectionResult
from support_agent.domain.responses import GeneratedSupportResponse
from support_agent.infrastructure.llm.base import LLMClient
from support_agent.prompts.response_prompts import build_response_generation_prompt
from support_agent.utils.cache import TimedLRUCache


class ResponseGenerator:
    """Generates persona-adaptive answers that are strictly grounded in retrieved context."""

    def __init__(
        self,
        llm_client: LLMClient,
        minimum_retrieval_confidence: float = 0.35,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 300,
        cache_max_items: int = 256,
    ) -> None:
        self._llm_client = llm_client
        self._minimum_retrieval_confidence = minimum_retrieval_confidence
        self._cache = (
            TimedLRUCache(maxsize=cache_max_items, ttl_seconds=cache_ttl_seconds)
            if cache_enabled
            else None
        )

    def generate(
        self,
        question: str,
        persona_result: PersonaDetectionResult,
        retrieval_result: HybridRetrievalResult,
    ) -> GeneratedSupportResponse:
        usable_chunks = self._usable_chunks(retrieval_result.results)
        retrieval_confidence = self._retrieval_confidence(usable_chunks)
        final_confidence = round(min(persona_result.confidence, retrieval_confidence), 3)

        if not usable_chunks:
            return self._insufficient_context_response(
                persona_result=persona_result,
                confidence=0.0,
                reason="No retrieved context was available.",
            )

        if retrieval_confidence < self._minimum_retrieval_confidence:
            return self._insufficient_context_response(
                persona_result=persona_result,
                confidence=final_confidence,
                reason="Retrieved context confidence is below the configured threshold.",
            )

        system_prompt, user_prompt = build_response_generation_prompt(
            question=question,
            persona=persona_result.persona,
            chunks=usable_chunks,
        )
        cache_key = self._cache_key(question, persona_result.persona, usable_chunks)
        if self._cache is not None:
            cached_response = self._cache.get(cache_key)
            if cached_response is not None:
                return cached_response

        answer = self._llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        answer = self._ensure_citations(answer, usable_chunks)

        response = GeneratedSupportResponse(
            answer=answer,
            persona=persona_result.persona,
            confidence=final_confidence,
            citations=self._citations(usable_chunks),
            retrieved_chunks=usable_chunks,
            used_context=True,
            requires_escalation=False,
        )

        if self._cache is not None:
            self._cache.set(cache_key, response)

        return response

    def _cache_key(self, question: str, persona: object, chunks: list[RetrievedChunk]) -> str:
        citation_digest = ";".join(
            f"{chunk.citation}:{chunk.score:.4f}" for chunk in chunks
        )
        return f"{question}|{persona}|{citation_digest}"

    def _insufficient_context_response(
        self,
        persona_result: PersonaDetectionResult,
        confidence: float,
        reason: str,
    ) -> GeneratedSupportResponse:
        return GeneratedSupportResponse(
            answer=(
                "I do not have enough support documentation to answer this safely. "
                "This should be escalated to a human support specialist."
            ),
            persona=persona_result.persona,
            confidence=confidence,
            citations=[],
            retrieved_chunks=[],
            used_context=False,
            requires_escalation=True,
            escalation_reason=reason,
        )

    def _usable_chunks(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        seen: set[str] = set()
        usable: list[RetrievedChunk] = []
        for chunk in chunks:
            if not chunk.chunk.text.strip():
                continue
            if chunk.chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk.chunk_id)
            usable.append(chunk)
        return usable

    def _retrieval_confidence(self, chunks: list[RetrievedChunk]) -> float:
        if not chunks:
            return 0.0
        best_score = max(chunk.score for chunk in chunks)
        supporting_evidence = min(len(chunks) / 4, 1.0) * 0.1
        return round(min(0.99, best_score + supporting_evidence), 3)

    def _ensure_citations(self, answer: str, chunks: list[RetrievedChunk]) -> str:
        citations = self._citations(chunks)
        if any(citation in answer for citation in citations):
            return answer
        return f"{answer.rstrip()}\n\nSources: {', '.join(citations)}"

    @staticmethod
    def _citations(chunks: list[RetrievedChunk]) -> list[str]:
        seen: set[str] = set()
        citations: list[str] = []
        for chunk in chunks:
            if chunk.citation not in seen:
                seen.add(chunk.citation)
                citations.append(chunk.citation)
        return citations
