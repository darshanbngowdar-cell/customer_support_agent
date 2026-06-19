# Architecture

TODO: Describe the production architecture, module boundaries, and workflow graph.

## Retrieval-Augmented Generation Subsystem

The retrieval subsystem is designed as a reusable set of interfaces and concrete adapters.
Document loading, chunking, vector storage, lexical retrieval, and rank fusion are separated
so each component can be tested or replaced independently.

### Document Loading

`DocumentLoader` supports:

- PDF files with page-level metadata from `pypdf`
- Markdown files with first-heading section metadata
- TXT files with file-level section metadata
- DOCX files split by heading sections

Every loaded document preserves:

- `source`
- `file_name`
- `file_type`
- `page_number`, when available
- `section_name`, when available

### Chunking

`DynamicDocumentChunker` uses LangChain's `RecursiveCharacterTextSplitter`.
Chunk size is selected dynamically from document length:

- small documents use smaller chunks
- large documents use larger chunks
- overlap is capped at one quarter of the selected chunk size

Each chunk receives:

- deterministic `chunk_id`
- deterministic `content_hash`
- original metadata
- `chunk_index`
- applied chunk size and overlap

Duplicate chunks are removed before indexing.

### Dense Retrieval

`ChromaVectorStore` persists chunks in ChromaDB and embeds text with Sentence Transformers.
Dense retrieval returns normalized similarity scores, raw distances, citations, and metadata.

### BM25 Retrieval

`BM25Retriever` is an in-memory lexical retriever over indexed chunks. It uses standard BM25
term frequency, inverse document frequency, and document-length normalization.

### Hybrid Retrieval

`HybridRetriever` runs dense and BM25 retrieval independently, then combines rankings with
`ReciprocalRankFusion`.

The fused result includes:

- final hybrid score
- dense score, when present
- BM25 score, when present
- citation string
- retrieved chunk metadata

### Configuration

Retrieval behavior is controlled through environment variables:

- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `MIN_CHUNK_SIZE`
- `MAX_CHUNK_SIZE`
- `DENSE_TOP_K`
- `BM25_TOP_K`
- `FUSION_TOP_K`
- `RRF_K`
- `DENSE_WEIGHT`
- `BM25_WEIGHT`
- `RETRIEVAL_CONFIDENCE_THRESHOLD`

## Persona Detection Strategy

Persona detection is implemented by `PersonaDetector` as a modular classifier over
`PersonaDefinition` objects. Each persona definition contains:

- persona name
- natural-language description
- response style guidance
- positive indicators
- optional negative indicators
- tie-break priority

The detector currently uses deterministic lexical scoring so the project can run and test
without an API key. The same definitions are also rendered into prompt templates by
`build_persona_classification_prompt`, which allows the workflow to move to an LLM-backed
classifier later without changing the persona model.

Classification flow:

1. Normalize the latest user message and recent conversation history.
2. Score every persona definition from matched indicators.
3. Weight phrase indicators above single-token indicators.
4. Select the strongest persona with priority-based tie breaking.
5. Convert relative evidence into a confidence score from 0 to 1.
6. Apply fallback rules when confidence is below threshold or no evidence is found.

Fallback behavior defaults to `Frustrated User`, because empathetic and simple support
responses are the safest low-confidence tone. Messages with strong emotional punctuation or
urgent language receive a slightly stronger frustrated-user fallback confidence.

Adding a future persona requires adding a new `PersonaDefinition`. The detector does not
need new branching logic for each persona.

## Response Generation Strategy

Response generation is handled by `ResponseGenerator`. It accepts the user question, the
detected persona, and the hybrid retrieval result. The component is intentionally strict:
it refuses to answer when no retrieved context is available or when retrieval confidence is
below the configured threshold.

Prompt management lives in `prompts/response_prompts.py`. The module contains:

- a shared grounding system prompt
- one reusable response template per persona
- context rendering with retrieval scores and citations

Persona behavior:

- `Technical Expert`: detailed, technical, root-cause oriented, step-by-step
- `Frustrated User`: empathetic, simple, reassuring, action-oriented
- `Business Executive`: concise, impact-focused, timeline-aware when supported

Anti-hallucination controls:

1. The system prompt forbids unsupported claims.
2. Empty retrieval results produce an escalation response instead of an answer.
3. Low-confidence retrieval produces an escalation response instead of an answer.
4. Citations are appended if the LLM output omits them.
5. Duplicate chunks are removed before prompt construction.

## LangGraph Application Workflow

LangGraph was chosen because this project is a stateful AI workflow, not a single function
call. The system needs explicit steps, shared state, retry policies, confidence gates, and
future extension points. LangGraph makes those transitions visible and testable while still
keeping each node as a normal Python component.

Current graph:

```text
User Input
  -> Persona Detection
  -> Query Optimization
  -> Hybrid Retrieval
  -> Context Validation
  -> Response Generation
  -> Confidence Evaluation
  -> Escalation Decision
  -> Human Handoff
  -> Final Response
```

Node responsibilities:

- `UserInputNode`: normalizes the message and initializes graph state.
- `PersonaDetectionNode`: classifies the customer persona.
- `QueryOptimizationNode`: creates a retrieval-friendly query using persona evidence and recent history.
- `HybridRetrievalNode`: runs dense plus BM25 retrieval through the retrieval service.
- `ContextValidationNode`: checks whether retrieved context is strong enough to answer.
- `ResponseGenerationNode`: produces a persona-specific grounded answer.
- `ConfidenceEvaluationNode`: combines persona, retrieval, context, and response confidence.
- `EscalationDecisionNode`: decides whether human support is required.
- `HumanHandoffNode`: creates a structured handoff summary when escalation is needed.
- `FinalResponseNode`: prepares the final response object for callers.

Retries are configured at the graph level for retrieval and response generation, because
those nodes are most likely to depend on external systems such as vector databases or LLM
providers. Future nodes can be inserted by adding a node class and wiring an edge in
`SupportAgentWorkflow`.

## Escalation Engine

Escalation is handled by `EscalationEngine`, a configurable rule engine separate from
LangGraph node wiring. It escalates for:

- low retrieval confidence
- no relevant documents
- repeated dissatisfaction
- billing issues
- legal issues
- sensitive account issues
- unknown or undocumented requests
- explicit response-generator escalation requests

The engine returns an `EscalationDecision` with trigger categories, human-readable reasons,
and confidence. When escalation is required, it generates a JSON-ready
`HumanHandoffSummary` containing:

- persona
- issue summary
- conversation history
- retrieved documents
- actions attempted
- confidence
- recommendation
- timestamp

## Conversation Memory

Conversation memory is implemented with LangGraph checkpointing plus an explicit
`ConversationMemoryState` domain model. `SupportAgentWorkflow.compile(use_memory=True)`
attaches a `MemorySaver` checkpointer, and `SupportAgentService` passes the session id as
LangGraph's `thread_id`. This lets the graph recover prior state across follow-up turns
without requiring callers to manually resend the full conversation.

The memory layer stores:

- session id
- completed user-assistant turns
- retrieved document citations
- persisted persona
- per-turn confidence
- timestamps

Memory is managed by `ConversationMemoryManager` rather than being embedded directly in UI
code. That keeps the policy for trimming, persona reuse, and state updates testable.

Follow-up support:

- `UserInputNode` restores trimmed session history from memory when no external history is provided.
- `PersonaDetectionNode` reuses the persisted persona when the latest message has weak evidence.
- `QueryOptimizationNode` expands short follow-up questions with recent history and recently retrieved documents.
- `FinalResponseNode` writes the completed turn back into memory.

Token optimization:

- `ConversationMemoryState.trimmed_history()` estimates prompt tokens using a lightweight character heuristic.
- Recent turns are selected from newest to oldest until the configured token budget is reached.
- Long-running sessions retain bounded turns and bounded retrieved-document citations.

Configuration:

- `MEMORY_MAX_TURNS`
- `MEMORY_TOKEN_BUDGET`
