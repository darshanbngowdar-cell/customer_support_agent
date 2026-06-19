import re
from collections import defaultdict

from support_agent.domain.personas import (
    DEFAULT_PERSONA_DEFINITIONS,
    PersonaDefinition,
    PersonaDetectionResult,
    PersonaType,
)
from support_agent.prompts.persona_prompts import build_persona_classification_prompt


class PersonaDetector:
    """Extensible persona classifier with prompt support and deterministic fallbacks."""

    def __init__(
        self,
        definitions: list[PersonaDefinition] | None = None,
        minimum_confidence: float = 0.35,
        fallback_persona: PersonaType = PersonaType.FRUSTRATED_USER,
    ) -> None:
        self._definitions = definitions or list(DEFAULT_PERSONA_DEFINITIONS)
        self._minimum_confidence = minimum_confidence
        self._fallback_persona = fallback_persona

    @property
    def definitions(self) -> list[PersonaDefinition]:
        return list(self._definitions)

    def build_prompt(
        self,
        message: str,
        conversation_history: list[str] | None = None,
    ) -> tuple[str, str]:
        return build_persona_classification_prompt(
            message=message,
            definitions=self._definitions,
            conversation_history=conversation_history,
        )

    def detect(
        self,
        message: str,
        conversation_history: list[str] | None = None,
    ) -> PersonaDetectionResult:
        candidate_scores = self._score_candidates(message, conversation_history or [])
        if not candidate_scores:
            return self._fallback_result(message, "No persona indicators were found.")

        best_persona, best_data = max(
            candidate_scores.items(),
            key=lambda item: (item[1]["score"], item[1]["priority"]),
        )
        confidence = self._confidence(best_data["score"], candidate_scores)
        matched_indicators = sorted(best_data["indicators"])

        if confidence < self._minimum_confidence:
            return self._fallback_result(
                message,
                "Persona evidence was below the configured confidence threshold.",
            )

        return PersonaDetectionResult(
            persona=best_persona,
            confidence=confidence,
            matched_indicators=matched_indicators,
            reasoning=(
                f"Classified as {best_persona.value} from matched indicators: "
                f"{', '.join(matched_indicators)}."
            ),
            used_fallback=False,
        )

    def _score_candidates(
        self,
        message: str,
        conversation_history: list[str],
    ) -> dict[PersonaType, dict[str, object]]:
        text = self._normalize(" ".join([*conversation_history[-3:], message]))
        scores: dict[PersonaType, dict[str, object]] = defaultdict(
            lambda: {"score": 0.0, "indicators": set(), "priority": 0}
        )

        for definition in self._definitions:
            persona_data = scores[definition.persona]
            persona_data["priority"] = definition.priority
            for indicator in definition.positive_indicators:
                if self._matches_indicator(text, indicator):
                    weight = self._indicator_weight(indicator)
                    persona_data["score"] = float(persona_data["score"]) + weight
                    indicators = persona_data["indicators"]
                    if isinstance(indicators, set):
                        indicators.add(indicator)

            for indicator in definition.negative_indicators:
                if self._matches_indicator(text, indicator):
                    persona_data["score"] = max(0.0, float(persona_data["score"]) - 0.5)

        return {
            persona: data
            for persona, data in scores.items()
            if float(data["score"]) > 0 and data["indicators"]
        }

    def _fallback_result(self, message: str, reason: str) -> PersonaDetectionResult:
        emotional_fallback = self._has_emotional_signal(message)
        persona = PersonaType.FRUSTRATED_USER if emotional_fallback else self._fallback_persona
        confidence = 0.35 if emotional_fallback else 0.25
        matched = ["emotional punctuation"] if emotional_fallback else []
        return PersonaDetectionResult(
            persona=persona,
            confidence=confidence,
            matched_indicators=matched,
            reasoning=f"{reason} Applied fallback persona: {persona.value}.",
            used_fallback=True,
        )

    @staticmethod
    def _confidence(
        best_score: object,
        candidate_scores: dict[PersonaType, dict[str, object]],
    ) -> float:
        best = float(best_score)
        total = sum(float(data["score"]) for data in candidate_scores.values())
        if total == 0:
            return 0.0
        margin = best / total
        evidence_boost = min(best / 4.0, 0.25)
        return round(min(0.99, margin * 0.75 + evidence_boost), 3)

    @staticmethod
    def _indicator_weight(indicator: str) -> float:
        if indicator == "!":
            return 0.25
        if " " in indicator:
            return 1.4
        return 1.0

    @staticmethod
    def _matches_indicator(text: str, indicator: str) -> bool:
        normalized_indicator = PersonaDetector._normalize(indicator)
        if normalized_indicator == "!":
            return "!" in text
        if " " in normalized_indicator:
            return normalized_indicator in text
        return re.search(rf"\b{re.escape(normalized_indicator)}\b", text) is not None

    @staticmethod
    def _has_emotional_signal(message: str) -> bool:
        return message.count("!") >= 2 or bool(re.search(r"\b(help|please|urgent)\b", message.lower()))

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())
