from __future__ import annotations

import json

import typer

from support_agent.application.agent_service import SupportAgentService
from support_agent.application.persona_detector import PersonaDetector
from support_agent.application.retrieval_service import RetrievalService
from support_agent.application.response_generator import ResponseGenerator
from support_agent.config.settings import get_settings
from support_agent.domain.exceptions import (
    DependencyInitializationError,
    LLMRequestError,
    PromptInjectionError,
    RateLimitExceededError,
    SupportAgentError,
)
from support_agent.graph.dependencies import SupportGraphDependencies
from support_agent.graph.workflow import SupportAgentWorkflow
from support_agent.infrastructure.factories import RetrievalSystemFactory
from support_agent.infrastructure.llm import MockLLMClient, OpenAIClient
from support_agent.infrastructure.telemetry.logger import configure_logging, log
from support_agent.utils.health import HealthChecker
from support_agent.utils.rate_limiter import RateLimiter

app = typer.Typer(help="Support Agent production CLI")


def _create_llm_client(settings):
    if settings.openai_api_key:
        return OpenAIClient(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_model,
            timeout=settings.openai_request_timeout,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            api_base=settings.openai_api_base,
        )

    log.warning(
        "SUPPORT_AGENT_OPENAI_API_KEY is not configured; falling back to mock LLM client"
    )
    return MockLLMClient()


def _build_service(settings):
    factory = RetrievalSystemFactory(settings)
    llm_client = _create_llm_client(settings)
    response_generator = ResponseGenerator(
        llm_client=llm_client,
        minimum_retrieval_confidence=settings.retrieval_confidence_threshold,
        cache_enabled=settings.cache_enabled,
        cache_ttl_seconds=settings.cache_ttl_seconds,
        cache_max_items=settings.cache_max_items,
    )
    dependencies = SupportGraphDependencies(
        persona_detector=PersonaDetector(),
        retrieval_service=RetrievalService(factory.create_hybrid_retriever()),
        response_generator=response_generator,
        escalation_engine=factory.create_escalation_engine(),
        memory_manager=factory.create_memory_manager(),
        context_validation_threshold=settings.retrieval_confidence_threshold,
    )
    compiled_graph = SupportAgentWorkflow(dependencies).compile(use_memory=True)
    return SupportAgentService(
        compiled_graph=compiled_graph,
        rate_limiter=RateLimiter(
            max_requests=settings.rate_limit_max_requests,
            window_seconds=settings.rate_limit_window_seconds,
        ),
    )


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    settings = get_settings()
    configure_logging(settings)
    if ctx.invoked_subcommand is None:
        typer.echo("Use one of the support-agent commands: run, health")
        raise typer.Exit(code=0)


@app.command()
def run(
    message: str = typer.Option(..., help="Question to ask the support agent."),
    session_id: str = typer.Option("default", help="Session identifier for rate limiting."),
    conversation_history: list[str] = typer.Option(
        None,
        "--history",
        help="Conversation history entries. Use multiple times for multiple turns.",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or text.",
    ),
) -> None:
    settings = get_settings()
    configure_logging(settings)
    try:
        service = _build_service(settings)
        response = service.handle_message(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history or [],
        )
        if output_format.lower() == "text":
            output = (
                f"Answer:\n{response.answer}\n\n"
                f"Persona: {response.persona.value}\n"
                f"Confidence: {response.confidence:.2f}\n"
                f"Escalation required: {response.requires_escalation}\n"
                f"Citations: {', '.join(response.citations) or 'none'}"
            )
            typer.echo(output)
        else:
            typer.echo(json.dumps(response.model_dump(mode="json"), indent=2))
    except (DependencyInitializationError, LLMRequestError, PromptInjectionError, RateLimitExceededError) as exc:
        log.error("request_failed", error=str(exc))
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except SupportAgentError as exc:
        log.exception("support_agent_failure", error=str(exc))
        typer.secho("Internal support agent error. Check logs for details.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    except Exception as exc:
        log.exception("unexpected_error", error=str(exc))
        typer.secho("Unexpected error. Please contact the administrator.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=3)


@app.command()
def health(deep: bool = typer.Option(False, help="Perform a deep dependency health check."), quiet: bool = typer.Option(False, help="Print minimal output for automation.")) -> None:
    settings = get_settings()
    configure_logging(settings)
    checker = HealthChecker(settings)
    try:
        report = checker.run(deep=deep)
        if not quiet:
            typer.echo(json.dumps(report, indent=2))
        raise typer.Exit(code=0)
    except SupportAgentError as exc:
        log.error("health_check_failed", error=str(exc))
        if not quiet:
            typer.secho(f"Health check failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    typer.echo("persona-support-agent 0.1.0")

