Demo: Quick end-to-end example

This demo builds a tiny knowledge base from a few short markdown files and launches the Streamlit demo app preloaded with the demo vector store.

Requirements

- Python 3.11+
- Install dev dependencies:

```bash
python -m pip install -e .[dev]
```

Run the demo ingestion (creates `data/vector_store/demo`):

```bash
python examples/demo/ingest_demo.py
```

Launch the Streamlit demo (preloads demo store):

```bash
python -m support_agent.presentation.streamlit_app --vector-store data/vector_store/demo
```

Notes

- This demo uses a very small dataset for quick local runs.
- If `chromadb` is not available or configured, the demo falls back to a simple in-memory vector store.
