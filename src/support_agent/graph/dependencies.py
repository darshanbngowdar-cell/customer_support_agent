from dataclasses import dataclass, field

from support_agent.application.conversation_memory import ConversationMemoryManager
from support_agent.application.escalation_engine import EscalationEngine
from support_agent.application.persona_detector import PersonaDetector
from support_agent.application.response_generator import ResponseGenerator
from support_agent.application.retrieval_service import RetrievalService


@dataclass(frozen=True)
class GraphRetryConfig:
    """Retry settings for recoverable graph nodes."""

    max_attempts: int = 2


@dataclass(frozen=True)
class SupportGraphDependencies:
    """Runtime dependencies injected into graph nodes."""

    persona_detector: PersonaDetector
    retrieval_service: RetrievalService
    response_generator: ResponseGenerator
    escalation_engine: EscalationEngine = field(default_factory=EscalationEngine)
    memory_manager: ConversationMemoryManager = field(default_factory=ConversationMemoryManager)
    context_validation_threshold: float = 0.35
    retry_config: GraphRetryConfig = field(default_factory=GraphRetryConfig)
