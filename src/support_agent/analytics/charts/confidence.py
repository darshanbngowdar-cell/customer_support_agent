"""Average confidence visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import CHART_COLORS, apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_confidence_chart(summary: AnalyticsSummary) -> go.Figure:
    records = summary.records
    if not records:
        return empty_figure("Average Confidence")

    timestamps = [record.timestamp for record in records]
    scores = [record.confidence_score for record in records]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=scores,
            mode="lines+markers",
            name="Confidence",
            fill="tozeroy",
            line=dict(color=CHART_COLORS[2], width=2),
            marker=dict(size=7),
            hovertemplate="Run: %{x}<br>Confidence: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=summary.average_confidence,
        line_dash="dash",
        line_color="#64748b",
        annotation_text=f"Avg: {summary.average_confidence:.2f}",
        annotation_position="top left",
    )
    fig.update_layout(
        xaxis_title="Run Time",
        yaxis_title="Confidence Score",
        yaxis=dict(range=[0, 1.05]),
        showlegend=False,
    )
    return apply_layout(fig, "Average Confidence")
