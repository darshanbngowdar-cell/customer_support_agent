#!/usr/bin/env bash
set -euo pipefail

echo "Running tests..."
pytest -q

echo "All tests passed."
