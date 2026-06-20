# Known Limitations

## Retrieval and grounding

- The system relies on the current document index and may not answer correctly if relevant content is missing or poorly indexed.
- Hybrid retrieval quality depends on vector embeddings and BM25 ranking; edge cases may still produce low-confidence context.

## Persona classification

- Persona detection currently uses deterministic lexical rules and may misclassify subtle tone or complex user intent.
- Additional personas require manual definition updates.

## LLM risk factors

- The backend model may still produce unsafe or incorrect responses despite grounding controls.
- Prompt injection and hallucinations are mitigated but not eliminated.

## Deployment and scaling

- The default implementation is not optimized for high-concurrency production traffic.
- Vector storage and retrieval may need a dedicated external service for large-scale document collections.

## Data and privacy

- Conversation data is persisted in-memory or via LangGraph checkpoints; sensitive data handling must be audited for production use.
- No built-in compliance workflows for GDPR, HIPAA, or other regulations.
