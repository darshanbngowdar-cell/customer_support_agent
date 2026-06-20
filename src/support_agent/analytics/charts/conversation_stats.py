"""Conversation statistics visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import CHART_COLORS, apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_conversation_stats_chart(summary: AnalyticsSummary) -> go.Figure:
    stats = summary.conversation_stats
    if stats.total_runs == 0:
        return empty_figure("Conversation Statistics")

    metrics = [
        "Total Runs",
        "Unique Sessions",
        "Total Turns",
        "Avg Turns / Session",
        "Avg Confidence",
        "Escalation Rate",
    ]
    values = [
        stats.total_runs,
        stats.unique_sessions,
        stats.total_turns,
        stats.average_turns_per_session,
        stats.average_confidence,
        stats.escalation_rate,
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=metrics,
                y=values,
                marker_color=[CHART_COLORS[index % len(CHART_COLORS)] for index in range(len(metrics))],
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        xaxis_title="Metric",
        yaxis_title="Value",
        showlegend=False,
    )
    return apply_layout(fig, "Conversation Statistics")
