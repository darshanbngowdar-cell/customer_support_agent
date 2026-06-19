from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from support_agent.graph.dependencies import SupportGraphDependencies
from support_agent.graph.nodes.confidence_node import ConfidenceEvaluationNode
from support_agent.graph.nodes.context_validation_node import ContextValidationNode
from support_agent.graph.nodes.escalation_node import EscalationDecisionNode
from support_agent.graph.nodes.final_response_node import FinalResponseNode
from support_agent.graph.nodes.handoff_node import HumanHandoffNode
from support_agent.graph.nodes.persona_node import PersonaDetectionNode
from support_agent.graph.nodes.query_optimization_node import QueryOptimizationNode
from support_agent.graph.nodes.response_node import ResponseGenerationNode
from support_agent.graph.nodes.retrieval_node import HybridRetrievalNode
from support_agent.graph.nodes.user_input_node import UserInputNode
from support_agent.graph.state import SupportAgentState


USER_INPUT = "user_input"
PERSONA_DETECTION = "persona_detection"
QUERY_OPTIMIZATION = "query_optimization"
HYBRID_RETRIEVAL = "hybrid_retrieval"
CONTEXT_VALIDATION = "context_validation"
RESPONSE_GENERATION = "response_generation"
CONFIDENCE_EVALUATION = "confidence_evaluation"
ESCALATION_DECISION = "escalation_decision_node"
HUMAN_HANDOFF = "human_handoff"
FINAL_RESPONSE = "final_response_node"


class SupportAgentWorkflow:
    """Builds the modular LangGraph workflow for the support agent."""

    def __init__(self, dependencies: SupportGraphDependencies) -> None:
        self._dependencies = dependencies

    def compile(self, use_memory: bool = True):
        graph = StateGraph(SupportAgentState)
        retry_policy = RetryPolicy(
            max_attempts=self._dependencies.retry_config.max_attempts,
            retry_on=Exception,
        )

        graph.add_node(USER_INPUT, UserInputNode(self._dependencies.memory_manager))
        graph.add_node(
            PERSONA_DETECTION,
            PersonaDetectionNode(
                self._dependencies.persona_detector,
                self._dependencies.memory_manager,
            ),
        )
        graph.add_node(QUERY_OPTIMIZATION, QueryOptimizationNode())
        graph.add_node(
            HYBRID_RETRIEVAL,
            HybridRetrievalNode(self._dependencies.retrieval_service),
            retry=retry_policy,
        )
        graph.add_node(CONTEXT_VALIDATION, ContextValidationNode())
        graph.add_node(
            RESPONSE_GENERATION,
            ResponseGenerationNode(self._dependencies.response_generator),
            retry=retry_policy,
        )
        graph.add_node(CONFIDENCE_EVALUATION, ConfidenceEvaluationNode())
        graph.add_node(
            ESCALATION_DECISION,
            EscalationDecisionNode(self._dependencies.escalation_engine),
        )
        graph.add_node(HUMAN_HANDOFF, HumanHandoffNode(self._dependencies.escalation_engine))
        graph.add_node(FINAL_RESPONSE, FinalResponseNode(self._dependencies.memory_manager))

        graph.add_edge(START, USER_INPUT)
        graph.add_edge(USER_INPUT, PERSONA_DETECTION)
        graph.add_edge(PERSONA_DETECTION, QUERY_OPTIMIZATION)
        graph.add_edge(QUERY_OPTIMIZATION, HYBRID_RETRIEVAL)
        graph.add_edge(HYBRID_RETRIEVAL, CONTEXT_VALIDATION)
        graph.add_edge(CONTEXT_VALIDATION, RESPONSE_GENERATION)
        graph.add_edge(RESPONSE_GENERATION, CONFIDENCE_EVALUATION)
        graph.add_edge(CONFIDENCE_EVALUATION, ESCALATION_DECISION)
        graph.add_edge(ESCALATION_DECISION, HUMAN_HANDOFF)
        graph.add_edge(HUMAN_HANDOFF, FINAL_RESPONSE)
        graph.add_edge(FINAL_RESPONSE, END)

        checkpointer = MemorySaver() if use_memory else None
        return graph.compile(checkpointer=checkpointer)
