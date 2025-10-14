install:
	uv sync --all-extras
	$(MAKE) install-hooks

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

# Git hooks
install-hooks:
	mkdir -p .git/hooks
	cp -f scripts/pre-commit .git/hooks/
	chmod +x .git/hooks/pre-commit
	@echo "Git pre-commit hook installed successfully."

.PHONY: start format lint lint-fix check