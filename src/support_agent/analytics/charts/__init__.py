"""Modular Plotly chart builders for the analytics dashboard."""

from support_agent.analytics.charts.confidence import build_confidence_chart
from support_agent.analytics.charts.conversation_stats import build_conversation_stats_chart
from support_agent.analytics.charts.escalation import build_escalation_chart
from support_agent.analytics.charts.latency import build_latency_chart
from support_agent.analytics.charts.persona_distribution import build_persona_distribution_chart
from support_agent.analytics.charts.retrieval_scores import build_retrieval_scores_chart
from support_agent.analytics.charts.top_documents import build_top_documents_chart

__all__ = [
    "build_confidence_chart",
    "build_conversation_stats_chart",
    "build_escalation_chart",
    "build_latency_chart",
    "build_persona_distribution_chart",
    "build_retrieval_scores_chart",
    "build_top_documents_chart",
]
