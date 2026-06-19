from support_agent.application.persona_detector import PersonaDetector
from support_agent.domain.personas import PersonaDefinition, PersonaType


def test_detects_technical_expert_from_api_language() -> None:
    detector = PersonaDetector()

    result = detector.detect(
        "Can you explain the API authentication failure and include the HTTP error code logs?"
    )

    assert result.persona == PersonaType.TECHNICAL_EXPERT
    assert result.confidence >= 0.35
    assert "api" in result.matched_indicators
    assert not result.used_fallback


def test_detects_frustrated_user_from_emotional_language() -> None:
    detector = PersonaDetector()

    result = detector.detect("I've tried everything and it is still not working! This is urgent!")

    assert result.persona == PersonaType.FRUSTRATED_USER
    assert result.confidence >= 0.35
    assert "urgent" in result.matched_indicators
    assert not result.used_fallback


def test_detects_business_executive_from_impact_language() -> None:
    detector = PersonaDetector()

    result = detector.detect(
        "What is the business impact, customer impact, and ETA for full resolution?"
    )

    assert result.persona == PersonaType.BUSINESS_EXECUTIVE
    assert result.confidence >= 0.35
    assert "business impact" in result.matched_indicators
    assert not result.used_fallback


def test_uses_fallback_when_evidence_is_weak() -> None:
    detector = PersonaDetector()

    result = detector.detect("Hello, I have a question.")

    assert result.persona == PersonaType.FRUSTRATED_USER
    assert result.used_fallback
    assert result.confidence < 0.35


def test_prompt_contains_dynamic_persona_catalog() -> None:
    detector = PersonaDetector()

    system_prompt, user_prompt = detector.build_prompt("Need help with webhook logs.")

    assert "persona classifier" in system_prompt
    assert "Technical Expert" in user_prompt
    assert "Frustrated User" in user_prompt
    assert "Business Executive" in user_prompt
    assert "Need help with webhook logs." in user_prompt


def test_future_persona_can_be_added_without_detector_changes() -> None:
    custom_definition = PersonaDefinition(
        persona=PersonaType.TECHNICAL_EXPERT,
        description="Custom technical persona.",
        response_style=["Diagnostic"],
        positive_indicators=["graphql resolver"],
        priority=10,
    )
    detector = PersonaDetector(definitions=[custom_definition])

    result = detector.detect("The GraphQL resolver is returning null for the account node.")

    assert result.persona == PersonaType.TECHNICAL_EXPERT
    assert result.matched_indicators == ["graphql resolver"]
