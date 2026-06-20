import inspect
import pkgutil
import importlib
try:
    module = importlib.import_module('langchain')
    cls = getattr(module, 'LangChainPendingDeprecationWarning', None)
    print('langchain attr', cls)
except Exception as e:
    print('langchain import failed', e)

# Try to find the class in installed packages
candidates = ['langchain', 'langgraph', 'langchain.utils', 'langchain.pydantic_utils', 'langgraph.checkpoint.base', 'langgraph.checkpoint.serde.jsonplus']
for name in candidates:
    try:
        m = importlib.import_module(name)
        for k, v in vars(m).items():
            if isinstance(v, type) and v.__name__ == 'LangChainPendingDeprecationWarning':
                print('found in', name, v, v.__module__)
    except Exception as e:
        pass

# Search sys.modules
import sys
for nm, mod in list(sys.modules.items()):
    try:
        for k, v in vars(mod).items():
            if isinstance(v, type) and v.__name__ == 'LangChainPendingDeprecationWarning':
                print('found in sys.modules', nm, v, v.__module__)
    except Exception:
        pass
