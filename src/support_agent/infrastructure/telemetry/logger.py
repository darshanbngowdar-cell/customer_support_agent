from support_agent.logging.config import configure_logging as _configure_logging
from support_agent.logging.config import get_logger as _get_logger


def configure_logging(settings: object | None = None) -> None:
    """Compatibility wrapper used by CLI and other modules.

    Accepts an optional settings object for backwards compatibility but uses
    the centralized logging configuration under `support_agent.logging.config`.
    """
    _configure_logging()


# Expose a module-level `log` to match previous imports elsewhere in the codebase
log = _get_logger("support_agent")

