"""Most retrieved documents visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import CHART_COLORS, apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_top_documents_chart(summary: AnalyticsSummary, limit: int = 10) -> go.Figure:
    if not summary.document_retrieval_counts:
        return empty_figure("Most Retrieved Documents")

    ranked = sorted(
        summary.document_retrieval_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:limit]
    documents = [item[0] for item in ranked]
    counts = [item[1] for item in ranked]

    fig = go.Figure(
        data=[
            go.Bar(
                x=counts,
                y=documents,
                orientation="h",
                marker_color=CHART_COLORS[0],
                hovertemplate="Document: %{y}<br>Retrievals: %{x}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        xaxis_title="Retrieval Count",
        yaxis=dict(autorange="reversed"),
        showlegend=False,
    )
    return apply_layout(fig, "Most Retrieved Documents")
