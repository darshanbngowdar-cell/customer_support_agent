import warnings

# Suppress the LangChain pending deprecation warning during tests. The
# warning class is defined in `langchain_core._api.deprecation` (LangChain
# v0.1+), so attempt to import and filter by category for precision. Fall
# back to a message+module filter if the class is not present.
try:
    from langchain_core._api.deprecation import (
        LangChainPendingDeprecationWarning,
    )

    warnings.filterwarnings(
        "ignore",
        category=LangChainPendingDeprecationWarning,
    )
except Exception:
    warnings.filterwarnings(
        "ignore",
        message=r"The default value of `allowed_objects` will change",
        module=r"langgraph.checkpoint.*",
    )
