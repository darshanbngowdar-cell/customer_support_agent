from support_agent.domain.documents import HybridRetrievalResult
from support_agent.domain.escalation import (
    EscalationDecision,
    EscalationRuleConfig,
    EscalationTrigger,
)
from support_agent.domain.handoff import HumanHandoffSummary
from support_agent.domain.personas import PersonaDetectionResult
from support_agent.domain.responses import GeneratedSupportResponse


class EscalationEngine:
    """Configurable escalation engine for human-in-the-loop support."""

    def __init__(self, config: EscalationRuleConfig | None = None) -> None:
        self._config = config or EscalationRuleConfig()

    def evaluate(
        self,
        user_message: str,
        conversation_history: list[str],
        persona_result: PersonaDetectionResult,
        retrieval_result: HybridRetrievalResult,
        generated_response: GeneratedSupportResponse,
        overall_confidence: float,
        context_validation_reasons: list[str] | None = None,
    ) -> EscalationDecision:
        reasons: list[str] = []
        triggers: list[EscalationTrigger] = []
        message_blob = self._normalize(" ".join([*conversation_history, user_message]))
        best_retrieval_score = max((result.score for result in retrieval_result.results), default=0.0)

        if not retrieval_result.results:
            self._add(
                triggers,
                reasons,
                EscalationTrigger.NO_RELEVANT_DOCUMENTS,
                "No relevant support documents were retrieved.",
            )
        elif best_retrieval_score < self._config.retrieval_confidence_threshold:
            self._add(
                triggers,
                reasons,
                EscalationTrigger.LOW_RETRIEVAL_CONFIDENCE,
                "Retrieval confidence is below the configured threshold.",
            )

        dissatisfaction_count = self._count_matches(message_blob, self._config.dissatisfaction_keywords)
        if dissatisfaction_count >= self._config.max_dissatisfaction_signals:
            self._add(
                triggers,
                reasons,
                EscalationTrigger.REPEATED_DISSATISFACTION,
                "User shows repeated dissatisfaction or unresolved frustration.",
            )

        if self._contains_any(message_blob, self._config.billing_keywords):
            self._add(triggers, reasons, EscalationTrigger.BILLING_ISSUE, "Billing-sensitive issue detected.")

        if self._contains_any(message_blob, self._config.legal_keywords):
            self._add(triggers, reasons, EscalationTrigger.LEGAL_ISSUE, "Legal or compliance-sensitive issue detected.")

        if self._contains_any(message_blob, self._config.sensitive_account_keywords):
            self._add(
                triggers,
                reasons,
                EscalationTrigger.SENSITIVE_ACCOUNT_ISSUE,
                "Sensitive account or security issue detected.",
            )

        if self._contains_any(message_blob, self._config.unknown_request_keywords):
            self._add(
                triggers,
                reasons,
                EscalationTrigger.UNKNOWN_REQUEST,
                "Unknown or undocumented request detected.",
            )

        if generated_response.requires_escalation:
            self._add(
                triggers,
                reasons,
                EscalationTrigger.RESPONSE_REQUIRES_ESCALATION,
                generated_response.escalation_reason or "Response generator requested escalation.",
            )

        if overall_confidence < self._config.overall_confidence_threshold:
            reasons.append("Overall confidence is below the configured threshold.")

        for reason in context_validation_reasons or []:
            reasons.append(reason)

        unique_reasons = list(dict.fromkeys(reasons))
        unique_triggers = list(dict.fromkeys(triggers))
        return EscalationDecision(
            should_escalate=bool(unique_triggers or overall_confidence < self._config.overall_confidence_threshold),
            reasons=unique_reasons,
            triggers=unique_triggers,
            confidence=overall_confidence,
        )

    def build_handoff_summary(
        self,
        user_message: str,
        conversation_history: list[str],
        persona_result: PersonaDetectionResult,
        retrieval_result: HybridRetrievalResult,
        decision: EscalationDecision,
        actions_attempted: list[str],
    ) -> HumanHandoffSummary:
        return HumanHandoffSummary(
            persona=persona_result.persona,
            issue_summary=self._summarize_issue(user_message),
            conversation_history=conversation_history,
            retrieved_documents=retrieval_result.citations,
            attempted_steps=actions_attempted,
            confidence=decision.confidence,
            recommendation=self._recommendation(decision),
            escalation_reasons=decision.reasons,
        )

    @staticmethod
    def _add(
        triggers: list[EscalationTrigger],
        reasons: list[str],
        trigger: EscalationTrigger,
        reason: str,
    ) -> None:
        triggers.append(trigger)
        reasons.append(reason)

    @staticmethod
    def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _count_matches(text: str, keywords: tuple[str, ...]) -> int:
        return sum(1 for keyword in keywords if keyword in text)

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    @staticmethod
    def _summarize_issue(user_message: str) -> str:
        normalized = " ".join(user_message.split())
        return normalized[:240]

    @staticmethod
    def _recommendation(decision: EscalationDecision) -> str:
        if not decision.triggers:
            return "Review the conversation and continue support if needed."
        trigger_text = ", ".join(trigger.value for trigger in decision.triggers)
        return (
            "Route to a human support representative. Review the retrieved documents, "
            f"validate account-specific details, and address these escalation triggers: {trigger_text}."
        )
