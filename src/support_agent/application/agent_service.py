from __future__ import annotations

import time
from typing import Any

from support_agent.analytics.collector import AnalyticsCollector
from support_agent.analytics.store import AnalyticsStore
from support_agent.domain.exceptions import (
    InputValidationError,
    PromptInjectionError,
)
from support_agent.domain.request import SupportRequest
from support_agent.domain.responses import GeneratedSupportResponse
from support_agent.graph.state import SupportAgentState
from support_agent.infrastructure.telemetry.logger import log
from support_agent.utils.rate_limiter import RateLimiter
from support_agent.utils.security import sanitize_user_input


class SupportAgentService:
    """Application boundary for running the LangGraph support workflow."""

    def __init__(
        self,
        compiled_graph: Any,
        analytics_store: AnalyticsStore | None = None,
        record_analytics: bool = True,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._compiled_graph = compiled_graph
        self._analytics_store = analytics_store or AnalyticsStore()
        self._record_analytics = record_analytics
        self._rate_limiter = rate_limiter or RateLimiter()

    def _prepare_request(
        self,
        message: str,
        session_id: str,
        conversation_history: list[str] | None,
    ) -> SupportRequest:
        message = sanitize_user_input(message)
        if not message:
            raise InputValidationError("The request message cannot be empty.")

        conversation_history = [
            sanitize_user_input(item)
            for item in (conversation_history or [])
        ]
        request = SupportRequest(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history,
        )
        self._rate_limiter.validate(request.session_id)
        return request

    def _invoke_graph(
        self,
        request: SupportRequest,
    ) -> SupportAgentState:
        log.info(
            "executing_graph",
            session_id=request.session_id,
            message_length=len(request.message),
            conversation_turns=len(request.conversation_history),
        )
        final_state = self._compiled_graph.invoke(
            {
                "user_message": request.message,
                "session_id": request.session_id,
                "conversation_history": request.conversation_history,
            },
            config={"configurable": {"thread_id": request.session_id}},
        )
        if "final_response" not in final_state:
            raise PromptInjectionError("The workflow failed to produce a final response.")
        return final_state

    def handle_message(
        self,
        message: str,
        session_id: str = "default",
        conversation_history: list[str] | None = None,
    ) -> GeneratedSupportResponse:
        request = self._prepare_request(message, session_id, conversation_history)
        final_state = self._invoke_graph(request)
        return final_state["final_response"]

    def run(
        self,
        message: str,
        session_id: str = "default",
        conversation_history: list[str] | None = None,
    ) -> SupportAgentState:
        request = self._prepare_request(message, session_id, conversation_history)
        started_at = time.perf_counter()
        final_state = self._invoke_graph(request)
        latency_ms = (time.perf_counter() - started_at) * 1000
        metadata = dict(final_state.get("metadata", {}))
        metadata["latency_ms"] = round(latency_ms, 2)
        final_state["metadata"] = metadata

        if self._record_analytics:
            record = AnalyticsCollector.from_state(final_state, latency_ms)
            self._analytics_store.append(record)

        return final_state
