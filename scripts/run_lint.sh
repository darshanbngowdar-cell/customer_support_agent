#!/usr/bin/env bash
set -euo pipefail

echo "Running ruff..."
python -m ruff check .

echo "Running isort (check)..."
python -m isort --check-only --profile black .

echo "Running black (check)..."
python -m black --check .

echo "Running mypy..."
python -m mypy src

echo "Linting complete."
