from __future__ import annotations

from support_agent.analytics.models import AnalyticsRunRecord, AnalyticsSummary, ConversationStatistics
from support_agent.graph.state import SupportAgentState


class AnalyticsCollector:
    """Extracts dashboard metrics from completed workflow state."""

    @staticmethod
    def from_state(state: SupportAgentState, latency_ms: float) -> AnalyticsRunRecord:
        session_id = state.get("session_id", "default")
        persona_result = state.get("persona_result")
        retrieval_result = state.get("retrieval_result")
        escalation_decision = state.get("escalation_decision")
        memory_state = state.get("memory_state")

        persona = persona_result.persona.value if persona_result else "Unknown"
        persona_confidence = persona_result.confidence if persona_result else 0.0
        retrieval_scores = (
            [round(chunk.score, 6) for chunk in retrieval_result.results]
            if retrieval_result
            else []
        )
        retrieved_documents = retrieval_result.citations if retrieval_result else []
        escalated = bool(escalation_decision and escalation_decision.should_escalate)
        turn_count = len(memory_state.turns) if memory_state else 0

        return AnalyticsRunRecord(
            session_id=session_id,
            latency_ms=round(latency_ms, 2),
            confidence_score=state.get("confidence_score", 0.0),
            persona=persona,
            persona_confidence=persona_confidence,
            retrieval_scores=retrieval_scores,
            retrieved_documents=retrieved_documents,
            escalated=escalated,
            conversation_turn_count=turn_count,
            context_is_valid=state.get("context_is_valid", True),
        )

    @staticmethod
    def summarize(records: list[AnalyticsRunRecord]) -> AnalyticsSummary:
        if not records:
            return AnalyticsSummary()

        persona_counts: dict[str, int] = {}
        document_counts: dict[str, int] = {}
        session_turns: dict[str, int] = {}
        escalation_count = 0
        total_latency = 0.0
        total_confidence = 0.0

        for record in records:
            persona_counts[record.persona] = persona_counts.get(record.persona, 0) + 1
            escalation_count += int(record.escalated)
            total_latency += record.latency_ms
            total_confidence += record.confidence_score
            session_turns[record.session_id] = max(
                session_turns.get(record.session_id, 0),
                record.conversation_turn_count,
            )
            for document in record.retrieved_documents:
                document_counts[document] = document_counts.get(document, 0) + 1

        total_runs = len(records)
        unique_sessions = len(session_turns)
        total_turns = sum(session_turns.values())

        conversation_stats = ConversationStatistics(
            total_runs=total_runs,
            unique_sessions=unique_sessions,
            total_turns=total_turns,
            average_turns_per_session=round(total_turns / unique_sessions, 2)
            if unique_sessions
            else 0.0,
            average_confidence=round(total_confidence / total_runs, 3),
            escalation_rate=round(escalation_count / total_runs, 3),
        )

        return AnalyticsSummary(
            records=records,
            average_latency_ms=round(total_latency / total_runs, 2),
            average_confidence=round(total_confidence / total_runs, 3),
            escalation_count=escalation_count,
            persona_counts=persona_counts,
            document_retrieval_counts=document_counts,
            conversation_stats=conversation_stats,
        )
