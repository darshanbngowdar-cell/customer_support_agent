"""Shared Plotly styling for analytics dashboard charts."""

from __future__ import annotations

import plotly.graph_objects as go

CHART_COLORS = [
    "#2563eb",
    "#7c3aed",
    "#059669",
    "#d97706",
    "#dc2626",
    "#0891b2",
]

CHART_LAYOUT = dict(
    template="plotly_white",
    margin=dict(l=40, r=20, t=50, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
)


def apply_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(title=dict(text=title, x=0.0, xanchor="left"), **CHART_LAYOUT)
    return fig


def empty_figure(title: str, message: str = "No data available yet.") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#64748b"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return apply_layout(fig, title)
