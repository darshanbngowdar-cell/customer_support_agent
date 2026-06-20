PYTHON=python
POETRY=poetry

.PHONY: install test lint format type docs

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

test:
	pytest -q

lint:
	ruff check .

format:
	black .
	isort .

type:
	mypy src tests

docs:
	@echo "Build docs not configured; see docs/*.md"
