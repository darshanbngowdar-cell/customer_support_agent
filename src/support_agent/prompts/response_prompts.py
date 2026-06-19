from support_agent.domain.documents import RetrievedChunk
from support_agent.domain.personas import PersonaType


GROUNDING_SYSTEM_PROMPT = """\
You are a grounded customer support assistant.
Use only the retrieved support context provided by the application.
Do not use prior knowledge, guesses, or assumptions.
If the context does not contain enough information, say that the issue should be escalated.
Every factual claim must be supported by the retrieved context.
Include source citations exactly as provided.
"""


TECHNICAL_EXPERT_RESPONSE_TEMPLATE = """\
Persona: Technical Expert
Required style:
- Detailed and technical
- Explain likely root cause only if supported by context
- Provide step-by-step troubleshooting
- Include configuration, API, logs, or error details only when present in context

Customer question:
{question}

Retrieved context:
{context}

Write a grounded answer with citations.
"""


FRUSTRATED_USER_RESPONSE_TEMPLATE = """\
Persona: Frustrated User
Required style:
- Empathetic and reassuring
- Simple language
- Action-oriented
- Avoid unnecessary jargon

Customer question:
{question}

Retrieved context:
{context}

Write a grounded answer with citations.
"""


BUSINESS_EXECUTIVE_RESPONSE_TEMPLATE = """\
Persona: Business Executive
Required style:
- Concise
- Explain business impact only when supported by context
- Include timeline or ETA only when supported by context
- Use minimal technical jargon

Customer question:
{question}

Retrieved context:
{context}

Write a grounded answer with citations.
"""


PERSONA_RESPONSE_TEMPLATES: dict[PersonaType, str] = {
    PersonaType.TECHNICAL_EXPERT: TECHNICAL_EXPERT_RESPONSE_TEMPLATE,
    PersonaType.FRUSTRATED_USER: FRUSTRATED_USER_RESPONSE_TEMPLATE,
    PersonaType.BUSINESS_EXECUTIVE: BUSINESS_EXECUTIVE_RESPONSE_TEMPLATE,
}


def render_retrieved_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        (
            f"[{index}] Citation: {chunk.citation}\n"
            f"Retrieval score: {chunk.score:.4f}\n"
            f"Text:\n{chunk.chunk.text}"
        )
        for index, chunk in enumerate(chunks, start=1)
    )


def build_response_generation_prompt(
    question: str,
    persona: PersonaType,
    chunks: list[RetrievedChunk],
) -> tuple[str, str]:
    template = PERSONA_RESPONSE_TEMPLATES[persona]
    return (
        GROUNDING_SYSTEM_PROMPT,
        template.format(
            question=question,
            context=render_retrieved_context(chunks),
        ),
    )
