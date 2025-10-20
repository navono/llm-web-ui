install:
	uv sync --all-extras
	$(MAKE) install-hooks

start:
	uv run -m src.main run

start-dev:
	@chmod +x scripts/dev-server.sh
	uv run watchfiles --ignore-paths "./src/__pycache__" --sigint-timeout 5 --sigkill-timeout 10 "bash scripts/dev-server.sh" "./src"

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
	cp -f scripts/pre-commit.sh .git/hooks/
	chmod +x .git/hooks/pre-commit.sh
	@echo "Git pre-commit hook installed successfully."

.PHONY: start start-dev format lint lint-fix check