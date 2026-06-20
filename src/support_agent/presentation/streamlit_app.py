"""Streamlit multi-page frontend for the support agent."""

from __future__ import annotations

import json
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Any

import streamlit as st
from pydantic import SecretStr

from support_agent.analytics.dashboard import AnalyticsDashboard
from support_agent.analytics.sample_data import generate_sample_records
from support_agent.analytics.store import AnalyticsStore
from support_agent.application.agent_service import SupportAgentService
from support_agent.application.ingestion_service import IngestionService
from support_agent.application.persona_detector import PersonaDetector
from support_agent.application.response_generator import ResponseGenerator
from support_agent.application.retrieval_service import RetrievalService
from support_agent.config.settings import Settings, get_settings
from support_agent.domain.exceptions import (
    DependencyInitializationError,
    LLMRequestError,
    PromptInjectionError,
    RateLimitExceededError,
    SupportAgentError,
)
from support_agent.graph.dependencies import SupportGraphDependencies
from support_agent.graph.workflow import SupportAgentWorkflow
from support_agent.infrastructure.factories import RetrievalSystemFactory
from support_agent.infrastructure.llm import MockLLMClient, OpenAIClient
from support_agent.infrastructure.vectorstores.chroma_store import ChromaVectorStore
from support_agent.utils.rate_limiter import RateLimiter

PAGE_HOME = "🏠 Home"
PAGE_AI = "💬 AI Assistant"
PAGE_KB = "📄 Knowledge Base"
PAGE_ANALYTICS = "📊 Analytics"
PAGE_SETTINGS = "⚙️ Settings"
PAGE_ABOUT = "ℹ️ About"

SUPPORTED_UPLOAD_TYPES = ["pdf", "docx", "txt"]

st.set_page_config(
    page_title="Persona Support Agent",
    page_icon="🤖",
    layout="wide",
)


def settings_to_key(settings: Settings) -> str:
    payload = settings.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True)


@st.cache_resource
def create_agent_service(settings_payload: str, refresh_token: int) -> SupportAgentService:
    settings = Settings(**json.loads(settings_payload))
    factory = RetrievalSystemFactory(settings)
    llm_client = create_llm_client(settings)
    response_generator = ResponseGenerator(
        llm_client=llm_client,
        minimum_retrieval_confidence=settings.retrieval_confidence_threshold,
        cache_enabled=settings.cache_enabled,
        cache_ttl_seconds=settings.cache_ttl_seconds,
        cache_max_items=settings.cache_max_items,
    )
    dependencies = SupportGraphDependencies(
        persona_detector=PersonaDetector(minimum_confidence=settings.persona_minimum_confidence),
        retrieval_service=RetrievalService(factory.create_hybrid_retriever()),
        response_generator=response_generator,
        escalation_engine=factory.create_escalation_engine(),
        memory_manager=factory.create_memory_manager(),
        context_validation_threshold=settings.retrieval_confidence_threshold,
    )
    compiled_graph = SupportAgentWorkflow(dependencies).compile(use_memory=True)
    return SupportAgentService(
        compiled_graph=compiled_graph,
        rate_limiter=RateLimiter(
            max_requests=settings.rate_limit_max_requests,
            window_seconds=settings.rate_limit_window_seconds,
        ),
    )


@st.cache_resource
def create_ingestion_service(settings_payload: str, refresh_token: int) -> IngestionService:
    settings = Settings(**json.loads(settings_payload))
    factory = RetrievalSystemFactory(settings)
    return IngestionService(
        document_loader=factory.create_document_loader(),
        chunker=factory.create_chunker(),
        vector_store=factory.create_vector_store(),
    )


@st.cache_resource
def create_vector_store(settings_payload: str, refresh_token: int) -> ChromaVectorStore:
    settings = Settings(**json.loads(settings_payload))
    factory = RetrievalSystemFactory(settings)
    return factory.create_vector_store()


def create_llm_client(settings: Settings) -> Any:
    if settings.openai_api_key is not None:
        return OpenAIClient(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_model,
            timeout=settings.openai_request_timeout,
            temperature=settings.openai_temperature,
            top_p=settings.openai_top_p,
            max_tokens=settings.openai_max_tokens,
            api_base=settings.openai_api_base,
        )

    st.warning(
        "OpenAI API key is not configured. The assistant will use a local mock LLM for preview purposes."
    )
    return MockLLMClient()


def initialize_session() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = "streamlit"
    if "settings_state" not in st.session_state:
        active = get_settings()
        st.session_state.settings_state = {
            "openai_api_key": active.openai_api_key.get_secret_value()
            if active.openai_api_key
            else "",
            "openai_model": active.openai_model,
            "temperature": active.openai_temperature,
            "top_p": active.openai_top_p,
            "max_tokens": active.openai_max_tokens,
            "dense_top_k": active.dense_top_k,
            "bm25_top_k": active.bm25_top_k,
            "fusion_top_k": active.fusion_top_k,
            "retrieval_confidence_threshold": active.retrieval_confidence_threshold,
            "persona_minimum_confidence": active.persona_minimum_confidence,
            "escalation_confidence_threshold": active.escalation_low_confidence_threshold,
            "validation_message": "",
        }
    if "service_refresh_token" not in st.session_state:
        st.session_state.service_refresh_token = 0
    if "kb_refresh_token" not in st.session_state:
        st.session_state.kb_refresh_token = 0


def refresh_service() -> None:
    st.session_state.service_refresh_token += 1


def refresh_kb() -> None:
    st.session_state.kb_refresh_token += 1


def build_ui_settings() -> Settings:
    base = get_settings()
    state = st.session_state.settings_state
    config = base.model_dump(mode="json")
    overrides = {
        "openai_api_key": SecretStr(state["openai_api_key"]) if state["openai_api_key"] else base.openai_api_key,
        "openai_model": state["openai_model"],
        "openai_temperature": state["temperature"],
        "openai_top_p": state["top_p"],
        "openai_max_tokens": state["max_tokens"],
        "dense_top_k": state["dense_top_k"],
        "bm25_top_k": state["bm25_top_k"],
        "fusion_top_k": state["fusion_top_k"],
        "retrieval_confidence_threshold": state["retrieval_confidence_threshold"],
        "persona_minimum_confidence": state["persona_minimum_confidence"],
        "escalation_low_confidence_threshold": state["escalation_confidence_threshold"],
    }
    config.update(overrides)
    return Settings(**config)


def get_agent_service() -> SupportAgentService:
    settings = build_ui_settings()
    payload = settings_to_key(settings)
    return create_agent_service(payload, st.session_state.service_refresh_token)


def get_ingestion_service() -> IngestionService:
    settings = build_ui_settings()
    payload = settings_to_key(settings)
    return create_ingestion_service(payload, st.session_state.kb_refresh_token)


def get_vector_store() -> ChromaVectorStore:
    settings = build_ui_settings()
    payload = settings_to_key(settings)
    return create_vector_store(payload, st.session_state.kb_refresh_token)


def validate_api_key() -> None:
    settings = build_ui_settings()
    if not settings.openai_api_key:
        st.warning("Enter an API key before validating.")
        return

    try:
        client = OpenAIClient(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_model,
            timeout=settings.openai_request_timeout,
            temperature=settings.openai_temperature,
            top_p=settings.openai_top_p,
            max_tokens=settings.openai_max_tokens,
            api_base=settings.openai_api_base,
        )
        client.ping()
        st.success("OpenAI API key validated successfully.")
    except SupportAgentError as exc:
        st.error(f"API key validation failed: {exc}")
    except Exception as exc:
        st.error(f"Unable to validate API credentials: {exc}")


def format_source(source: str) -> str:
    return Path(source).name


def save_uploaded_files(files: list[Any], raw_dir: Path) -> int:
    raw_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for uploaded_file in files:
        file_name = Path(uploaded_file.name).name
        dest = raw_dir / file_name
        suffix = 1
        while dest.exists():
            dest = raw_dir / f"{Path(file_name).stem}_{suffix}{Path(file_name).suffix}"
            suffix += 1
        dest.write_bytes(uploaded_file.getvalue())
        saved += 1
    return saved


def list_raw_documents(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        return []
    return sorted(
        [path for path in data_dir.rglob("*") if path.is_file() and path.suffix.lower().lstrip(".") in SUPPORTED_UPLOAD_TYPES],
        key=lambda path: path.name,
    )


def list_indexed_sources(chroma: ChromaVectorStore) -> list[dict[str, Any]]:
    chunks = chroma.list_chunks()
    source_counter: Counter[str] = Counter()
    file_types: dict[str, str] = {}
    for chunk in chunks:
        source = format_source(str(chunk.metadata.get("source", "unknown")))
        source_counter[source] += 1
        file_types[source] = str(chunk.metadata.get("file_type", "unknown"))

    return [
        {"source": source, "chunks": count, "type": file_types.get(source, "unknown")}
        for source, count in source_counter.items()
    ]


def render_page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.write(subtitle)


def render_home_page() -> None:
    render_page_header(
        "Persona Support Agent",
        "A grounded, persona-aware customer support assistant with hybrid retrieval, human escalation, and analytics.",
    )

    st.markdown("---")
    left, right = st.columns([2, 1])
    with left:
        st.header("Modern support for customer-facing workflows")
        st.write(
            "This application blends retrieval-augmented generation, persona-aware responses, and human escalation so your support team answers confidently and consistently."
        )
        st.markdown(
            "- **Persona-aware responses** adapt tone and style to customer sentiment.\n"
            "- **Hybrid retrieval** combines dense embeddings with lexical BM25 ranking.\n"
            "- **Escalation guardrails** prevent unsafe or unsupported answers.\n"
            "- **Analytics** tracks performance, confidence, and escalation trends."
        )

    with right:
        st.image(
            "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=900&q=80",
            caption="Intelligent customer support",
            use_column_width=True,
        )

    st.markdown("---")
    st.subheader("What this project delivers")
    cards = [
        ("Smart Conversation", "AI-powered chat with persona detection and citation-aware answers."),
        ("Knowledge Base", "Upload documents and index support articles, policies, and manuals."),
        ("Safety & Escalation", "Detect sensitive queries and route them for human review."),
        ("Analytics", "Track usage, confidence, personas, and escalation patterns."),
    ]
    cols = st.columns(4)
    for column, card in zip(cols, cards):
        column.subheader(card[0])
        column.write(card[1])

    st.markdown("---")
    st.subheader("Architecture Overview")
    st.write(
        "The application separates the support workflow into four layers: input handling, persona classification, hybrid retrieval, and grounded response generation. Escalation and memory are managed independently to keep the agent safe and explainable."
    )
    st.markdown(
        "- **Input**: user requests enter through a modern UI and pass sanitization checks.\n"
        "- **Persona**: the system classifies sentiment and selects an answer style.\n"
        "- **Retrieval**: documents are indexed in Chroma and searched with both embeddings and BM25.\n"
        "- **Response**: answers are generated with a grounded prompt and citation policy.\n"
        "- **Escalation**: low-confidence, legal, billing, or safety issues are flagged for human review."
    )

    st.markdown("---")
    st.subheader("Technology Stack")
    st.write(
        "Python, Streamlit, OpenAI, LangGraph, ChromaDB, Sentence Transformers, Pydantic, and Plotly analytics."
    )
    st.markdown(
        "- **Frontend:** Streamlit\n"
        "- **Retrieval:** ChromaDB + BM25\n"
        "- **LLM:** OpenAI or local mock client\n"
        "- **Workflow:** LangGraph\n"
        "- **Settings:** Pydantic + environment variables\n"
        "- **Analytics:** JSON-backed metrics store"
    )


def render_chat_message(entry: dict[str, Any]) -> None:
    role = entry["role"]
    with st.chat_message(role):
        st.write(entry["message"])
        if role == "assistant":
            st.markdown(
                f"**Persona:** {entry.get('persona', 'Unknown')}  \
**Confidence:** {entry.get('confidence', 0.0):.2f}"
            )
            if entry.get("requires_escalation"):
                st.warning("This interaction has been flagged for human escalation.")
            if entry.get("citations"):
                st.markdown("**Citations:**")
                for citation in entry["citations"]:
                    st.markdown(f"- {citation}")
            if entry.get("retrieved_documents"):
                st.markdown("**Retrieved documents:**")
                for document in entry["retrieved_documents"]:
                    st.markdown(f"- {format_source(document)}")


def render_ai_assistant_page() -> None:
    render_page_header(
        "AI Assistant",
        "Ask support questions, inspect citations, and see persona-aware responses in real time.",
    )

    left, right = st.columns([3, 1])
    with left:
        query = st.chat_input("Ask a support question...")
        if query:
            st.session_state.chat_input = query

        if st.button("Send") and st.session_state.get("chat_input"):
            send_user_message(st.session_state.pop("chat_input"))

        if st.button("Clear chat"):
            st.session_state.chat_history = []
            st.session_state.session_id = f"streamlit-{int(time.time())}"
            refresh_service()

        if st.session_state.chat_history:
            for entry in st.session_state.chat_history:
                render_chat_message(entry)
        else:
            st.info("Start a conversation by asking a question above.")

    with right:
        st.subheader("Quick facts")
        st.write("- Uses hybrid retrieval and persona-aware generation.")
        st.write("- Includes citation tracking and escalation warnings.")
        st.write("- Settings are adjustable in the sidebar.")


def send_user_message(message: str) -> None:
    service = get_agent_service()
    history = []
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            history.append(entry["message"])
        elif entry["role"] == "assistant":
            history.append(f"Assistant: {entry['message']}")

    st.session_state.chat_history.append({"role": "user", "message": message})
    placeholder = st.empty()
    try:
        response = service.handle_message(
            message=message,
            session_id=st.session_state.session_id,
            conversation_history=history,
        )
        streamed = ""
        for token in response.answer.split():
            streamed += token + " "
            placeholder.markdown(streamed)
            time.sleep(0.02)
        placeholder.markdown(streamed)
        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "message": streamed.strip(),
                "persona": response.persona.value,
                "confidence": response.confidence,
                "citations": response.citations,
                "retrieved_documents": [
                    chunk.chunk.metadata.get("source", "unknown")
                    for chunk in response.retrieved_chunks
                ],
                "requires_escalation": response.requires_escalation,
            }
        )
    except RateLimitExceededError as exc:
        st.error(str(exc))
    except PromptInjectionError as exc:
        st.error(str(exc))
    except SupportAgentError as exc:
        st.error(f"Support agent error: {exc}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")


def render_knowledge_base_page() -> None:
    render_page_header(
        "Knowledge Base",
        "Upload documents, rebuild the vector database, and inspect indexed content.",
    )

    settings = build_ui_settings()
    raw_path = Path(settings.data_dir)
    raw_path.mkdir(parents=True, exist_ok=True)

    uploaded_files = st.file_uploader(
        "Upload support documents",
        type=SUPPORTED_UPLOAD_TYPES,
        accept_multiple_files=True,
        help="Drag and drop PDF, DOCX, or TXT files to add them to the knowledge base.",
    )

    if uploaded_files:
        count = save_uploaded_files(uploaded_files, raw_path)
        st.success(f"Saved {count} document{'s' if count != 1 else ''} to {raw_path}.")
        refresh_kb()

    with st.expander("Knowledge base actions", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Index documents"):
                with st.spinner("Indexing documents..."):
                    try:
                        imported = get_ingestion_service().ingest_directory(raw_path)
                        st.success(f"Indexed {imported} new chunks from the raw documents.")
                        refresh_kb()
                    except Exception as exc:
                        st.error(f"Indexing failed: {exc}")
        with col2:
            if st.button("Rebuild vector database"):
                with st.spinner("Rebuilding vector store..."):
                    try:
                        store_dir = Path(settings.vector_store_dir)
                        if store_dir.exists():
                            shutil.rmtree(store_dir)
                        imported = get_ingestion_service().ingest_directory(raw_path)
                        st.success(f"Rebuilt the vector database with {imported} chunks.")
                        refresh_kb()
                    except Exception as exc:
                        st.error(f"Rebuild failed: {exc}")

    st.markdown("---")
    st.subheader("Raw documents")
    raw_docs = list_raw_documents(raw_path)
    if raw_docs:
        selected = st.multiselect(
            "Select documents to delete",
            [path.name for path in raw_docs],
        )
        if selected and st.button("Delete selected raw files"):
            for name in selected:
                target = raw_path / name
                if target.exists():
                    target.unlink()
            st.success(f"Deleted {len(selected)} raw document{'s' if len(selected) != 1 else ''}.")
            refresh_kb()
    else:
        st.write("No raw documents found. Upload files to begin indexing.")

    st.markdown("---")
    st.subheader("Indexed documents")
    try:
        vector_store = get_vector_store()
        indexed_sources = list_indexed_sources(vector_store)
        if indexed_sources:
            st.dataframe(indexed_sources, hide_index=True)
            st.write(f"Total indexed chunks: {len(vector_store.list_chunks())}")
        else:
            st.write("No documents are currently indexed. Run the indexing workflow above.")
    except Exception as exc:
        st.error(f"Unable to load indexed documents: {exc}")


def render_analytics_page() -> None:
    render_page_header(
        "Analytics",
        "Review conversation metrics, persona distribution, and escalation trends.",
    )

    store = AnalyticsStore()
    col, action_col = st.columns([3, 1])
    with action_col:
        if st.button("Load sample analytics"):
            store.save(generate_sample_records())
            st.experimental_rerun()
        if st.button("Clear analytics"):
            store.clear()
            st.experimental_rerun()

    dashboard = AnalyticsDashboard(store)
    summary = dashboard.load_summary()
    charts = dashboard.build_charts(summary)

    stats = st.columns(3)
    stats[0].metric("Total runs", summary.conversation_stats.total_runs)
    stats[1].metric("Average confidence", f"{summary.average_confidence:.2f}")
    stats[2].metric("Escalations", summary.escalation_count)

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts["latency"], use_container_width=True)
        st.plotly_chart(charts["retrieval_scores"], use_container_width=True)
    with right:
        st.plotly_chart(charts["confidence"], use_container_width=True)
        st.plotly_chart(charts["persona_distribution"], use_container_width=True)

    st.markdown("---")
    st.plotly_chart(charts["escalation"], use_container_width=True)
    st.plotly_chart(charts["top_documents"], use_container_width=True)

    st.markdown("---")
    st.subheader("Raw analytics records")
    st.write([record.model_dump(mode="json") for record in summary.records])


def render_settings_page() -> None:
    render_page_header(
        "Settings",
        "Control model behavior, retrieval thresholds, and escalation rules for the assistant.",
    )

    state = st.session_state.settings_state
    with st.form("settings_form"):
        st.subheader("Model configuration")
        state["openai_api_key"] = st.text_input(
            "OpenAI API Key", value=state["openai_api_key"], type="password"
        )
        state["openai_model"] = st.selectbox(
            "Model",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-3.5-turbo-16k"],
            index=["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-3.5-turbo-16k"].index(
                state["openai_model"]
            )
            if state["openai_model"] in ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-3.5-turbo-16k"]
            else 0,
        )
        state["temperature"] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=state["temperature"],
            step=0.05,
        )
        state["top_p"] = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=state["top_p"],
            step=0.01,
        )
        state["max_tokens"] = st.slider(
            "Max tokens",
            min_value=64,
            max_value=2048,
            value=state["max_tokens"],
            step=64,
        )

        st.subheader("Retrieval and escalation")
        state["dense_top_k"] = st.number_input(
            "Dense top K",
            min_value=1,
            max_value=20,
            value=state["dense_top_k"],
            step=1,
        )
        state["bm25_top_k"] = st.number_input(
            "BM25 top K",
            min_value=1,
            max_value=20,
            value=state["bm25_top_k"],
            step=1,
        )
        state["fusion_top_k"] = st.number_input(
            "Fusion top K",
            min_value=1,
            max_value=20,
            value=state["fusion_top_k"],
            step=1,
        )
        state["retrieval_confidence_threshold"] = st.slider(
            "Retrieval confidence threshold",
            min_value=0.0,
            max_value=1.0,
            value=state["retrieval_confidence_threshold"],
            step=0.01,
        )
        state["persona_minimum_confidence"] = st.slider(
            "Persona minimum confidence",
            min_value=0.0,
            max_value=1.0,
            value=state["persona_minimum_confidence"],
            step=0.01,
        )
        state["escalation_confidence_threshold"] = st.slider(
            "Escalation confidence threshold",
            min_value=0.0,
            max_value=1.0,
            value=state["escalation_confidence_threshold"],
            step=0.01,
        )

        submitted = st.form_submit_button("Apply settings")
        if submitted:
            refresh_service()
            refresh_kb()
            st.success("Settings updated for this session.")

    if st.button("Validate API Key"):
        validate_api_key()

    st.markdown("---")
    st.info(
        "These settings apply to the current Streamlit session. To persist them globally, update `.env` or your environment variables."
    )


def render_about_page() -> None:
    render_page_header(
        "About",
        "Learn how the agent works and where to find source documentation.",
    )
    st.markdown(
        "### Architecture\nThe support agent is built as a modular Python application with a clear separation between presentation, application business logic, infrastructure adapters, and domain models."
    )
    st.markdown(
        "### Workflow\nThe request flow includes user input sanitization, persona detection, query optimization, hybrid retrieval, context validation, response generation, confidence evaluation, and escalation decisioning."
    )
    st.markdown(
        "### Technologies\n- Python 3.11\n- Streamlit\n- OpenAI / mock LLM\n- LangGraph workflow orchestration\n- ChromaDB for dense retrieval\n- BM25 lexical ranking\n- Pydantic for typed settings and domain models\n- Plotly analytics"
    )
    st.markdown(
        "### Resources\n- [GitHub repository](https://github.com/your-org/your-repo)\n- [Project documentation](https://github.com/your-org/your-repo#readme)\n- [Architecture docs](docs/architecture.md)"
    )
    st.markdown("---")
    st.write(
        "This application is intended as a flexible prototype for persona-aware customer support with grounded answers and safe escalation behavior."
    )


def render_sidebar() -> str:
    st.sidebar.title("Navigation")
    return st.sidebar.radio(
        "Go to",
        [PAGE_HOME, PAGE_AI, PAGE_KB, PAGE_ANALYTICS, PAGE_SETTINGS, PAGE_ABOUT],
        index=0,
    )


def main() -> None:
    initialize_session()
    active_page = render_sidebar()

    if active_page == PAGE_HOME:
        render_home_page()
    elif active_page == PAGE_AI:
        render_ai_assistant_page()
    elif active_page == PAGE_KB:
        render_knowledge_base_page()
    elif active_page == PAGE_ANALYTICS:
        render_analytics_page()
    elif active_page == PAGE_SETTINGS:
        render_settings_page()
    elif active_page == PAGE_ABOUT:
        render_about_page()


if __name__ == "__main__":
    main()
