from support_agent.application.escalation_engine import EscalationEngine
from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk, SupportDocumentChunk
from support_agent.domain.escalation import EscalationRuleConfig, EscalationTrigger
from support_agent.domain.personas import PersonaDetectionResult, PersonaType
from support_agent.domain.responses import GeneratedSupportResponse


def _persona() -> PersonaDetectionResult:
    return PersonaDetectionResult(
        persona=PersonaType.FRUSTRATED_USER,
        confidence=0.8,
        matched_indicators=["urgent"],
        reasoning="test",
    )


def _response(requires_escalation: bool = False) -> GeneratedSupportResponse:
    return GeneratedSupportResponse(
        answer="Grounded answer.",
        persona=PersonaType.FRUSTRATED_USER,
        confidence=0.8,
        citations=["support.md, section Help"],
        retrieved_chunks=[],
        used_context=True,
        requires_escalation=requires_escalation,
        escalation_reason="Generator requested escalation." if requires_escalation else None,
    )


def _retrieval(score: float = 0.8) -> HybridRetrievalResult:
    return HybridRetrievalResult(
        results=[
            RetrievedChunk(
                chunk=SupportDocumentChunk(
                    chunk_id="chunk-1",
                    text="Support guidance.",
                    metadata={"source": "support.md", "section_name": "Help"},
                    content_hash="hash-1",
                ),
                score=score,
                retrieval_method="hybrid_rrf",
            )
        ]
    )


def test_escalates_when_no_relevant_documents_exist() -> None:
    decision = EscalationEngine().evaluate(
        user_message="Can you help with this?",
        conversation_history=[],
        persona_result=_persona(),
        retrieval_result=HybridRetrievalResult(results=[]),
        generated_response=_response(requires_escalation=True),
        overall_confidence=0.2,
    )

    assert decision.should_escalate
    assert EscalationTrigger.NO_RELEVANT_DOCUMENTS in decision.triggers


def test_escalates_for_billing_legal_and_sensitive_account_issues() -> None:
    decision = EscalationEngine().evaluate(
        user_message="I need a refund and legal help because my account was hacked.",
        conversation_history=[],
        persona_result=_persona(),
        retrieval_result=_retrieval(),
        generated_response=_response(),
        overall_confidence=0.8,
    )

    assert EscalationTrigger.BILLING_ISSUE in decision.triggers
    assert EscalationTrigger.LEGAL_ISSUE in decision.triggers
    assert EscalationTrigger.SENSITIVE_ACCOUNT_ISSUE in decision.triggers


def test_escalates_for_repeated_dissatisfaction_and_unknown_requests() -> None:
    engine = EscalationEngine(EscalationRuleConfig(max_dissatisfaction_signals=2))

    decision = engine.evaluate(
        user_message="This is still not working again and the undocumented option is not covered.",
        conversation_history=["I tried everything and nothing works."],
        persona_result=_persona(),
        retrieval_result=_retrieval(),
        generated_response=_response(),
        overall_confidence=0.8,
    )

    assert EscalationTrigger.REPEATED_DISSATISFACTION in decision.triggers
    assert EscalationTrigger.UNKNOWN_REQUEST in decision.triggers


def test_handoff_summary_is_structured_json_ready() -> None:
    engine = EscalationEngine()
    decision = engine.evaluate(
        user_message="I need a billing refund.",
        conversation_history=["Previous message"],
        persona_result=_persona(),
        retrieval_result=_retrieval(),
        generated_response=_response(),
        overall_confidence=0.7,
    )

    handoff = engine.build_handoff_summary(
        user_message="I need a billing refund.",
        conversation_history=["Previous message"],
        persona_result=_persona(),
        retrieval_result=_retrieval(),
        decision=decision,
        actions_attempted=["Persona detection", "Hybrid retrieval"],
    )
    payload = handoff.to_json_dict()

    assert payload["persona"] == "Frustrated User"
    assert payload["issue_summary"] == "I need a billing refund."
    assert payload["retrieved_documents"] == ["support.md, section Help"]
    assert payload["confidence"] == 0.7
    assert "timestamp" in payload
