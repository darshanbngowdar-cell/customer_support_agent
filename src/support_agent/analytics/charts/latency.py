"""Response latency visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_latency_chart(summary: AnalyticsSummary) -> go.Figure:
    records = summary.records
    if not records:
        return empty_figure("Response Latency")

    timestamps = [record.timestamp for record in records]
    latencies = [record.latency_ms for record in records]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=latencies,
            mode="lines+markers",
            name="Latency",
            line=dict(color="#2563eb", width=2),
            marker=dict(size=7),
            hovertemplate="Run: %{x}<br>Latency: %{y:.1f} ms<extra></extra>",
        )
    )
    fig.add_hline(
        y=summary.average_latency_ms,
        line_dash="dash",
        line_color="#64748b",
        annotation_text=f"Avg: {summary.average_latency_ms:.1f} ms",
        annotation_position="top left",
    )
    fig.update_layout(
        xaxis_title="Run Time",
        yaxis_title="Latency (ms)",
        showlegend=False,
    )
    return apply_layout(fig, "Response Latency")
