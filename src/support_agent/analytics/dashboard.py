"""Analytics aggregation and dashboard assembly."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts import (
    build_confidence_chart,
    build_conversation_stats_chart,
    build_escalation_chart,
    build_latency_chart,
    build_persona_distribution_chart,
    build_retrieval_scores_chart,
    build_top_documents_chart,
)
from support_agent.analytics.collector import AnalyticsCollector
from support_agent.analytics.models import AnalyticsSummary
from support_agent.analytics.store import AnalyticsStore


class AnalyticsDashboard:
    """Builds a modular set of Plotly figures from persisted analytics records."""

    def __init__(self, store: AnalyticsStore | None = None) -> None:
        self._store = store or AnalyticsStore()

    def load_summary(self) -> AnalyticsSummary:
        records = self._store.load()
        return AnalyticsCollector.summarize(records)

    def build_charts(self, summary: AnalyticsSummary | None = None) -> dict[str, go.Figure]:
        resolved_summary = summary or self.load_summary()
        return {
            "latency": build_latency_chart(resolved_summary),
            "confidence": build_confidence_chart(resolved_summary),
            "retrieval_scores": build_retrieval_scores_chart(resolved_summary),
            "persona_distribution": build_persona_distribution_chart(resolved_summary),
            "escalation": build_escalation_chart(resolved_summary),
            "top_documents": build_top_documents_chart(resolved_summary),
            "conversation_stats": build_conversation_stats_chart(resolved_summary),
        }
