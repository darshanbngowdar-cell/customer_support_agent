"""Escalation count visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_escalation_chart(summary: AnalyticsSummary) -> go.Figure:
    records = summary.records
    if not records:
        return empty_figure("Escalation Count")

    timestamps = [record.timestamp for record in records]
    escalated = [1 if record.escalated else 0 for record in records]
    resolved = [0 if record.escalated else 1 for record in records]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=timestamps,
            y=resolved,
            name="Resolved",
            marker_color="#059669",
            hovertemplate="Run: %{x}<br>Status: Resolved<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=timestamps,
            y=escalated,
            name="Escalated",
            marker_color="#dc2626",
            hovertemplate="Run: %{x}<br>Status: Escalated<extra></extra>",
        )
    )
    fig.update_layout(
        barmode="stack",
        xaxis_title="Run Time",
        yaxis_title="Count",
        yaxis=dict(tickmode="linear", dtick=1, range=[0, max(1, max(escalated + resolved) + 0.5)]),
    )
    fig.add_annotation(
        text=f"Total escalations: {summary.escalation_count}",
        xref="paper",
        yref="paper",
        x=1.0,
        y=1.12,
        showarrow=False,
        font=dict(size=12, color="#64748b"),
        xanchor="right",
    )
    return apply_layout(fig, "Escalation Count")
