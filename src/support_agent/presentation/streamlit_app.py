"""Streamlit analytics dashboard for the support agent."""

from __future__ import annotations

import streamlit as st

from support_agent.analytics.dashboard import AnalyticsDashboard
from support_agent.analytics.models import AnalyticsSummary
from support_agent.analytics.sample_data import generate_sample_records
from support_agent.analytics.store import AnalyticsStore

st.set_page_config(
    page_title="Support Agent Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("Support Agent Analytics Dashboard")
st.caption("Modular Plotly visualizations for workflow performance and conversation metrics.")


@st.cache_resource
def get_store() -> AnalyticsStore:
    return AnalyticsStore()


@st.cache_data(show_spinner=False)
def load_summary(_store_path: str) -> tuple[AnalyticsSummary, int]:
    dashboard = AnalyticsDashboard(AnalyticsStore(_store_path))
    summary = dashboard.load_summary()
    return summary, len(summary.records)


def render_sidebar(store: AnalyticsStore) -> None:
    st.sidebar.header("Controls")
    if st.sidebar.button("Load sample data"):
        store.save(generate_sample_records())
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("Clear analytics"):
        store.clear()
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown(
        """
        **Metrics shown**
        - Response latency
        - Average confidence
        - Retrieval scores
        - Persona distribution
        - Escalation count
        - Most retrieved documents
        - Conversation statistics
        """
    )


def render_kpi_row(summary: AnalyticsSummary) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Runs", summary.conversation_stats.total_runs)
    col2.metric("Avg Latency (ms)", f"{summary.average_latency_ms:.1f}")
    col3.metric("Avg Confidence", f"{summary.average_confidence:.2f}")
    col4.metric("Escalations", summary.escalation_count)


def main() -> None:
    store = get_store()
    render_sidebar(store)

    summary, record_count = load_summary(str(store.path))
    dashboard = AnalyticsDashboard(store)
    charts = dashboard.build_charts(summary)

    if record_count == 0:
        st.info(
            "No analytics records yet. Run the support agent or click "
            "**Load sample data** in the sidebar to preview the dashboard."
        )

    render_kpi_row(summary)

    st.subheader("Performance")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts["latency"], use_container_width=True)
    with right:
        st.plotly_chart(charts["confidence"], use_container_width=True)

    st.subheader("Retrieval & Personas")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts["retrieval_scores"], use_container_width=True)
    with right:
        st.plotly_chart(charts["persona_distribution"], use_container_width=True)

    st.subheader("Escalations & Documents")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts["escalation"], use_container_width=True)
    with right:
        st.plotly_chart(charts["top_documents"], use_container_width=True)

    st.subheader("Conversation Statistics")
    st.plotly_chart(charts["conversation_stats"], use_container_width=True)

    with st.expander("Raw analytics records"):
        st.json([record.model_dump(mode="json") for record in summary.records])


if __name__ == "__main__":
    main()
