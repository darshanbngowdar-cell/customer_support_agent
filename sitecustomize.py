import warnings

# Apply a global startup filter to silence the LangChain pending deprecation
# warning emitted by langgraph/langchain internals. This runs very early (on
# interpreter startup) so it suppresses the message before modules import.
try:
    from langchain_core._api.deprecation import (
        LangChainPendingDeprecationWarning,
    )

    warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
except Exception:
    warnings.filterwarnings(
        "ignore",
        message=r"The default value of `allowed_objects` will change",
        module=r"langgraph.checkpoint.*",
    )
