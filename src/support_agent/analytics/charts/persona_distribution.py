"""Persona distribution visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import CHART_COLORS, apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_persona_distribution_chart(summary: AnalyticsSummary) -> go.Figure:
    if not summary.persona_counts:
        return empty_figure("Persona Distribution")

    personas = list(summary.persona_counts.keys())
    counts = list(summary.persona_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=personas,
                values=counts,
                hole=0.45,
                marker=dict(colors=CHART_COLORS[: len(personas)]),
                textinfo="label+percent",
                hovertemplate="%{label}<br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
    return apply_layout(fig, "Persona Distribution")
