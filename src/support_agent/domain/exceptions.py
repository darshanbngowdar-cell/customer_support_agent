from __future__ import annotations


class SupportAgentError(Exception):
    """Base exception for support agent runtime failures."""


class InputValidationError(SupportAgentError):
    """Raised when user input does not pass validation checks."""


class PromptInjectionError(SupportAgentError):
    """Raised when user input appears to contain prompt injection attempts."""


class RateLimitExceededError(SupportAgentError):
    """Raised when a session exceeds the configured rate limit."""


class LLMRequestError(SupportAgentError):
    """Raised when an LLM provider request fails."""


class DependencyInitializationError(SupportAgentError):
    """Raised when a required external dependency or configuration is invalid."""
