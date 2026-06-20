from datetime import UTC, datetime

from support_agent.analytics.collector import AnalyticsCollector
from support_agent.analytics.dashboard import AnalyticsDashboard
from support_agent.analytics.models import AnalyticsRunRecord
from support_agent.analytics.store import AnalyticsStore
from support_agent.domain.documents import HybridRetrievalResult, RetrievedChunk, SupportDocumentChunk
from support_agent.domain.escalation import EscalationDecision
from support_agent.domain.memory import ConversationMemoryState, ConversationTurn
from support_agent.domain.personas import PersonaDetectionResult, PersonaType
from support_agent.graph.state import SupportAgentState


def _sample_state(*, escalated: bool = False) -> SupportAgentState:
    return {
        "session_id": "session-1",
        "user_message": "Help with API auth",
        "conversation_history": [],
        "persona_result": PersonaDetectionResult(
            persona=PersonaType.TECHNICAL_EXPERT,
            confidence=0.88,
            matched_indicators=["api"],
            reasoning="Technical vocabulary detected.",
        ),
        "retrieval_result": HybridRetrievalResult(
            results=[
                RetrievedChunk(
                    chunk=SupportDocumentChunk(
                        chunk_id="chunk-1",
                        text="Auth docs",
                        metadata={"source": "api_authentication.md", "section_name": "Auth"},
                        content_hash="hash-1",
                    ),
                    score=0.82,
                    retrieval_method="hybrid_rrf",
                )
            ]
        ),
        "context_is_valid": not escalated,
        "confidence_score": 0.2 if escalated else 0.91,
        "escalation_decision": EscalationDecision(
            should_escalate=escalated,
            confidence=0.2 if escalated else 0.91,
        ),
        "memory_state": ConversationMemoryState(
            session_id="session-1",
            turns=[
                ConversationTurn(
                    user_message="Help with API auth",
                    assistant_response="Check credentials.",
                    persona=PersonaType.TECHNICAL_EXPERT,
                    retrieved_documents=["api_authentication.md, section Auth"],
                    confidence=0.91,
                    timestamp=datetime(2026, 6, 20, tzinfo=UTC),
                )
            ],
        ),
    }


def test_collector_extracts_metrics_from_state() -> None:
    record = AnalyticsCollector.from_state(_sample_state(), latency_ms=950.5)

    assert record.session_id == "session-1"
    assert record.latency_ms == 950.5
    assert record.persona == "Technical Expert"
    assert record.confidence_score == 0.91
    assert record.retrieval_scores == [0.82]
    assert record.retrieved_documents == ["api_authentication.md, section Auth"]
    assert record.escalated is False
    assert record.conversation_turn_count == 1


def test_collector_summarize_aggregates_records() -> None:
    records = [
        AnalyticsCollector.from_state(_sample_state(), latency_ms=900.0),
        AnalyticsCollector.from_state(_sample_state(escalated=True), latency_ms=1200.0),
    ]
    summary = AnalyticsCollector.summarize(records)

    assert summary.average_latency_ms == 1050.0
    assert summary.escalation_count == 1
    assert summary.persona_counts["Technical Expert"] == 2
    assert summary.document_retrieval_counts["api_authentication.md, section Auth"] == 2
    assert summary.conversation_stats.total_runs == 2


def test_store_persists_and_loads_records(tmp_path) -> None:
    store = AnalyticsStore(tmp_path / "metrics.json")
    record = AnalyticsCollector.from_state(_sample_state(), latency_ms=800.0)

    store.append(record)
    loaded = store.load()

    assert len(loaded) == 1
    assert loaded[0].session_id == "session-1"
    assert loaded[0].latency_ms == 800.0


def test_dashboard_builds_all_chart_modules(tmp_path) -> None:
    store = AnalyticsStore(tmp_path / "metrics.json")
    store.save([AnalyticsCollector.from_state(_sample_state(), latency_ms=800.0)])

    charts = AnalyticsDashboard(store).build_charts()

    assert set(charts) == {
        "latency",
        "confidence",
        "retrieval_scores",
        "persona_distribution",
        "escalation",
        "top_documents",
        "conversation_stats",
    }
    for figure in charts.values():
        assert figure.layout.title.text is not None
