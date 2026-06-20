# Installation

## Requirements

- Python 3.11 or 3.12
- Git
- Docker (optional for container deployment)

## Local setup

```bash
git clone https://github.com/<your-org>/customer_support_agent.git
cd customer_support_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Environment configuration

Copy the example environment file and set provider credentials:

```bash
cp .env.example .env
```

Required environment variables:

- `OPENAI_API_KEY` or `OPENAI_API_BASE` with a compatible provider
- `SUPPORT_AGENT_DEFAULT_PERSONA`
- `SUPPORT_AGENT_RETRIEVAL_CONFIDENCE_THRESHOLD`

Optional environment variables are documented in `src/support_agent/config/settings.py`.

## Run the CLI

```bash
python -m support_agent.presentation.cli run --message "How do I reset my password?"
```

## Run the Streamlit app

```bash
python -m support_agent.presentation.streamlit_app
```

## Run tests

```bash
pytest -q
```
