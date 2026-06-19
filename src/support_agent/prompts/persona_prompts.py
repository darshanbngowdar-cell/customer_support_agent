from support_agent.domain.personas import PersonaDefinition


PERSONA_CLASSIFICATION_SYSTEM_PROMPT = """\
You are a customer support persona classifier.
Classify the latest customer message into exactly one supported persona.
Return only valid JSON with:
- persona: one of the supported persona names
- confidence: number from 0 to 1
- reasoning: brief explanation grounded in the customer message
- matched_indicators: short list of observed indicators

Do not invent unsupported personas.
"""


PERSONA_CLASSIFICATION_USER_TEMPLATE = """\
Supported personas:
{persona_catalog}

Conversation history:
{conversation_history}

Latest customer message:
{message}
"""


def render_persona_catalog(definitions: list[PersonaDefinition]) -> str:
    return "\n\n".join(
        (
            f"Persona: {definition.persona.value}\n"
            f"Description: {definition.description}\n"
            f"Response style: {', '.join(definition.response_style)}\n"
            f"Indicators: {', '.join(definition.positive_indicators)}"
        )
        for definition in definitions
    )


def build_persona_classification_prompt(
    message: str,
    definitions: list[PersonaDefinition],
    conversation_history: list[str] | None = None,
) -> tuple[str, str]:
    history = "\n".join(conversation_history or []) or "No previous conversation."
    return (
        PERSONA_CLASSIFICATION_SYSTEM_PROMPT,
        PERSONA_CLASSIFICATION_USER_TEMPLATE.format(
            persona_catalog=render_persona_catalog(definitions),
            conversation_history=history,
            message=message,
        ),
    )
