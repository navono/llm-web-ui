install:
	uv sync --all-extras

start:
	uv run -m src.main run

format:
	uv run ruff format .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix . --unsafe-fixes

check:
	uv run ruff check .
	uv run ruff format --check .

.PHONY: start format lint lint-fix check