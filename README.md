# Persona-Adaptive Customer Support Agent

## Project Overview

TODO: Briefly describe the AI support agent, the problem it solves, and the assessment goals.

## Key Features

- TODO: Persona detection
- TODO: Retrieval-Augmented Generation
- TODO: Persona-adaptive response generation
- TODO: Configurable escalation workflow
- TODO: Human handoff summary
- TODO: CLI and Streamlit interfaces

## Tech Stack

TODO: List Python version, LLM provider, embedding provider, vector database, orchestration framework, UI, testing tools, and deployment tools.

## Architecture

```text
User Query
  -> Interface
  -> Agent Service
  -> LangGraph Workflow
  -> Persona Detection
  -> Knowledge Retrieval
  -> Grounded Response Generation
  -> Escalation Check
  -> Human Handoff Summary
```

TODO: Add architecture diagram and component explanation.

## Repository Structure

TODO: Explain the major folders and modules.

## Persona Detection Strategy

TODO: Explain classification method, prompt design, confidence scoring, and fallback behavior.

## RAG Pipeline Design

TODO: Explain document loading, chunking, embeddings, vector storage, metadata, and retrieval strategy.

Current retrieval subsystem:

- Loads PDF, Markdown, TXT, and DOCX files.
- Preserves source metadata, page numbers, section names, chunk indices, and file type.
- Uses LangChain `RecursiveCharacterTextSplitter` with dynamic chunk sizing.
- Creates deterministic chunk IDs and content hashes.
- Prevents duplicate chunks before indexing and when writing to ChromaDB.
- Embeds chunks with Sentence Transformers.
- Stores vectors and metadata in ChromaDB.
- Runs dense retrieval and BM25 retrieval independently.
- Combines rankings with Reciprocal Rank Fusion.
- Returns retrieval scores, source score breakdowns, and citations.

## Escalation Logic

TODO: Explain escalation triggers, configurable thresholds, and human handoff behavior.

## Setup Instructions

TODO: Add local setup steps.

## Environment Variables

TODO: Document required and optional environment variables.

## Running the Application

TODO: Add CLI and Streamlit commands.

## Knowledge Base

TODO: Describe the support documents under `data/raw`.

## Example Queries

TODO: Provide at least five example queries covering all personas and escalation.

## Evaluation

TODO: Explain persona, retrieval, and workflow evaluation scripts.

## Testing

TODO: Add test commands and coverage expectations.

## Docker

TODO: Explain Docker and Docker Compose usage.

## Known Limitations

TODO: Document current limitations and future improvements.

## Demo Recording Guide

TODO: Link to the demo script and recording checklist.
