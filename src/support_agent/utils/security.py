from __future__ import annotations

import re

from support_agent.domain.exceptions import PromptInjectionError

_PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|earlier) instructions",
    r"disregard (all )?(previous|prior|earlier) instructions",
    r"forget (all )?(previous|prior|earlier) instructions",
    r"override (all )?(previous|prior|earlier) instructions",
    r"^(system|assistant|user):",
    r"\bdo not follow\b",
    r"\bopenai\b",
    r"\bexecute\b.*\bcode\b",
    r"```",
    r"<script>",
]

_PROMPT_INJECTION_REGEX = re.compile("|".join(_PROMPT_INJECTION_PATTERNS), re.IGNORECASE)
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_user_input(message: str) -> str:
    """Normalize user input and reject prompt injection attempts."""
    if not isinstance(message, str):
        raise PromptInjectionError("User input must be a text string.")

    normalized = _CONTROL_CHAR_PATTERN.sub(" ", message).strip()
    if _PROMPT_INJECTION_REGEX.search(normalized):
        raise PromptInjectionError(
            "User input appears to include unsafe prompt manipulation instructions."
        )

    if len(normalized) > 2000:
        normalized = normalized[:2000]

    return normalized
