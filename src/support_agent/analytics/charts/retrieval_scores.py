"""Retrieval score visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from support_agent.analytics.charts.base import CHART_COLORS, apply_layout, empty_figure
from support_agent.analytics.models import AnalyticsSummary


def build_retrieval_scores_chart(summary: AnalyticsSummary) -> go.Figure:
    records = summary.records
    scored_records = [record for record in records if record.retrieval_scores]
    if not scored_records:
        return empty_figure("Retrieval Scores")

    labels: list[str] = []
    scores: list[float] = []
    colors: list[str] = []

    for index, record in enumerate(scored_records):
        for score in record.retrieval_scores:
            labels.append(f"Run {index + 1}")
            scores.append(score)
            colors.append(CHART_COLORS[index % len(CHART_COLORS)])

    fig = go.Figure()
    fig.add_trace(
        go.Box(
            y=scores,
            name="Retrieval Scores",
            marker_color=CHART_COLORS[0],
            boxmean="sd",
            hovertemplate="Score: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=scores,
            mode="markers",
            name="Chunk Scores",
            marker=dict(color=colors, size=8, opacity=0.75),
            hovertemplate="Run: %{x}<br>Score: %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Run",
        yaxis_title="Retrieval Score",
        yaxis=dict(range=[0, 1.05]),
        showlegend=False,
    )
    return apply_layout(fig, "Retrieval Scores")
