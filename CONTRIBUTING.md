# Contributing

Thank you for your interest in contributing to `customer_support_agent`.

## Ways to contribute

- Report bugs or unexpected behavior
- Suggest features or architectural improvements
- Improve documentation
- Add tests for missing coverage
- Fix lint or formatting issues

## Development setup

1. Clone the repository.
2. Create a virtual environment.
3. Install development dependencies.

Example:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Branching and pull requests

- Create a descriptive branch name, e.g. `feature/xxx`, `bugfix/xxx`, `docs/xxx`.
- Open a pull request against `main`.
- Provide a short summary of the change and any testing performed.
- Link related issues when applicable.

## Code style

This repository uses:

- `black` for formatting
- `isort` for import sorting
- `flake8` for linting
- `mypy` for type checking
- `pre-commit` for local hooks

Run the full checks locally before opening a PR:

```bash
pre-commit run --all-files
pytest
```

## Issue reports

A good bug report includes:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Relevant environment or configuration

## Documentation contributions

Please keep the documentation:

- clear and concise
- accurate to the current codebase
- linked from `README.md` when appropriate
