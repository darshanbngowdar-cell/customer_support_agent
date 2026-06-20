from support_agent.domain.documents import RetrievedChunk, SupportDocumentChunk
from support_agent.domain.personas import PersonaDefinition, PersonaType
from support_agent.prompts.persona_prompts import build_persona_classification_prompt, render_persona_catalog
from support_agent.prompts.response_prompts import build_response_generation_prompt


def test_render_persona_catalog_contains_persona_definitions() -> None:
    definitions = [
        PersonaDefinition(
            persona=PersonaType.TECHNICAL_EXPERT,
            description="Technical troubleshooting persona.",
            response_style=["detailed"],
            positive_indicators=["api", "error"],
            negative_indicators=[],
            priority=1,
        )
    ]

    catalog = render_persona_catalog(definitions)

    assert "Technical Expert" in catalog
    assert "Technical troubleshooting persona." in catalog
    assert "api, error" in catalog


def test_build_persona_classification_prompt_includes_message_and_history() -> None:
    definitions = [
        PersonaDefinition(
            persona=PersonaType.FRUSTRATED_USER,
            description="Empathetic support persona.",
            response_style=["simple"],
            positive_indicators=["urgent", "help"],
            negative_indicators=[],
            priority=1,
        )
    ]
    system_prompt, user_prompt = build_persona_classification_prompt(
        message="I need help now.",
        definitions=definitions,
        conversation_history=["First turn"],
    )

    assert "customer support persona classifier" in system_prompt.lower()
    assert "First turn" in user_prompt
    assert "I need help now." in user_prompt
    assert "Frustrated User" in user_prompt


def test_build_response_generation_prompt_includes_citations() -> None:
    chunks = [
        RetrievedChunk(
            chunk=SupportDocumentChunk(
                chunk_id="c1",
                text="Please reset your password.",
                metadata={"source": "reset.md", "page_number": 1},
                content_hash="h1",
            ),
            score=0.95,
            retrieval_method="hybrid_rrf",
        )
    ]
    system_prompt, user_prompt = build_response_generation_prompt(
        question="How do I reset my password?",
        persona=PersonaType.FRUSTRATED_USER,
        chunks=chunks,
    )

    assert "grounded customer support assistant" in system_prompt.lower()
    assert "How do I reset my password?" in user_prompt
    assert "Citation: reset.md, page 1" in user_prompt
