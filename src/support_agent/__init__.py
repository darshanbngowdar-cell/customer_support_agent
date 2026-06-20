

import warnings

# Suppress LangGraph/LangChain pending deprecation about checkpoint allowed_objects.
# The library emits a LangChainPendingDeprecationWarning suggesting to pass
# `allowed_objects` in future versions; silence it to keep test output clean.
try:
	from langgraph.checkpoint.base import LangChainPendingDeprecationWarning  # type: ignore

	warnings.filterwarnings(
		"ignore",
		category=LangChainPendingDeprecationWarning,
		message=r"The default value of `allowed_objects` will change",
	)
except Exception:
	# If langgraph isn't installed in some environments, nothing to do.
	pass

# As a fallback, filter by module+message to silence the same warning regardless
# of the concrete warning class implementation.
warnings.filterwarnings(
	"ignore",
	message=r"The default value of `allowed_objects` will change",
	module=r"langgraph.checkpoint.*",
)

