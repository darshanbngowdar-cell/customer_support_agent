# Project Showcase — Persona-Adaptive Customer Support Agent

This document is written for interviewers and senior engineers reviewing the repository. It summarizes the problem, architecture, AI pipeline, core engineering decisions, tradeoffs, deployment, and suggested talking points for interviews.

## Problem

Provide a safe, persona-aware customer support assistant that answers user questions using internal documentation while minimizing hallucinations and escalating to humans when needed.

Key requirements:
- Grounded answers with source citations
- Persona-adaptive tone and detail level
- Hybrid retrieval (dense + lexical) for robust coverage
- Auditable handoff and escalation
- Configurable, reproducible ingest and indexing pipeline

## Architecture (Clean + Hexagonal)

- Domain: immutable models (`domain/`) — personas, documents, responses, escalation rules.
- Application: use-cases and orchestrators (`application/`) — persona detector, retrieval orchestration, response generator, ingestion service.
- Infrastructure: adapters (`infrastructure/`) — LLM client, embeddings, vector store (Chroma), BM25, loaders, telemetry.
- Presentation: UIs and CLIs (`presentation/`) — Streamlit, CLI runner.
- Wiring: factories and DI container (`infrastructure/factories.py`, `infrastructure/di/container.py`).

The codebase favors small, focused modules with explicit interfaces to make component replacement and testing straightforward.

## AI Pipeline Overview

1. Input sanitization and validation
2. Persona detection (rule-based + classifier prompt)
3. Query optimization and expansion (local heuristics)
4. Hybrid retrieval: dense embeddings (Sentence Transformers) + BM25 lexical ranking
5. Reciprocal Rank Fusion (RRFusion) to combine scores
6. Context validation and deduplication
7. Grounded generation using carefully scoped prompts
8. Confidence evaluation and escalation decision
9. Persistent conversation memory and analytics

## Retrieval-augmented Generation (RAG)

- Documents are chunked deterministically with overlap to preserve context.
- Embeddings are produced via `SentenceTransformerEmbeddingProvider` and persisted into Chroma.
- BM25 runs locally against stored chunk text to capture lexical signals.
- Dense + BM25 scores are fused with configurable weights; top-k fused results are fed to the generator.

## LangGraph Usage

- LangGraph is used to represent and execute the end-to-end workflow as explicit nodes (persona detection, retrieval, generation, evaluation).
- This gives reproducibility for debugging, checkpointing, and snapshotting workflows during E2E tests.

## Persona Detection

- Multi-tier approach: lightweight heuristics for quick routing, prompt-based classification for ambiguous cases.
- Outputs a `PersonaDetectionResult(persona, confidence)` used by response generator to pick tone and detail.

## Human Escalation

- Escalation rules are configurable via `EscalationRuleConfig` and detect billing/legal/account issues.
- Low-confidence outputs or explicit user signals trigger an escalation workflow with an auditable handoff summary.

## Engineering Decisions & Tradeoffs

- Clean Architecture: added indirection for adapters to make the system testable and pluggable.
- Sentence Transformers for local embeddings: tradeoff between accuracy and latency; allows offline testing without paid APIs.
- Chroma as on-disk vector store for simplicity and reproducibility vs a managed vector DB in production.
- RRF fusion preserves complementary strengths of dense and lexical retrieval while remaining simple to implement.
- Structlog and DI: enable structured telemetry and easier runtime wiring for production systems.

## Performance & Scalability Considerations

- Improve retrieval latency by adding an in-memory ANN index or switching to a managed vector DB for high QPS.
- Add Redis caching for frequent queries and a Redis-backed BM25 index for larger corpora.
- Instrument Prometheus metrics (request latency, retrieval time, embedding time, LLM latency).

## Security & Validation

- Sanitize user input and token budget for prompts to reduce prompt injection risks.
- Use Secrets manager (not in repo) for API keys in production.

## Deployment

- `Dockerfile` and `docker-compose.yml` included. For production, use multi-stage builds, private registries, and a Kubernetes deployment with secrets and autoscaling.

## Future Improvements

- Add cross-encoder re-ranking for improved final ranking precision.
- Add active-learning loop to surface low-confidence queries to human review and automatically index corrected answers.
- Replace local Chroma with a scalable managed vector DB for production workloads.
- Add observability dashboards (Grafana) and SLO-based alerting.

## Interview Talking Points

- Explain why Clean Architecture helps with testability, onboarding, and long-term maintenance.
- Describe the RAG pipeline and the tradeoffs of dense vs lexical retrieval.
- Discuss prompt design choices to prevent hallucination and why citation-first responses are safer.
- Argue for using local embedding models during development to reduce cost and enable reproducible CI.
- Explain how escalation rules are designed to minimize false positives while ensuring safety for legal/billing issues.
- Outline how you'd scale the retrieval layer for 10k QPS and maintain cost control.

---

For a concise technical walkthrough, open `README.md` and the `docs/` folder. Use this file during interviews as your engineering narrative.
