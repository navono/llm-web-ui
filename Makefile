install:
	uv sync --all-extras
	$(MAKE) install-hooks

start:
	uv run -m src.main run

start-dev:
	@chmod +x scripts/dev-server.sh
	uv run watchfiles --ignore-paths "./src/__pycache__" --sigint-timeout 5 --sigkill-timeout 10 "bash scripts/dev-server.sh" "./src"

start-audio-server:
	cd packages/index-tts && uv run python openai-audio-server.py

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

# Docker targets for IndexTTS2
docker-build-indextts2:
	@echo "Building IndexTTS2 Docker image..."
	docker build -f docker/Dockerfile.indextts2 -t indextts2:latest .

docker-build-indextts2-proxy:
	@echo "Building IndexTTS2 Docker image with proxy..."
	docker build -f docker/Dockerfile.indextts2 \
		--build-arg HTTP_PROXY=http://172.18.32.1:18899 \
		--build-arg HTTPS_PROXY=http://172.18.32.1:18899 \
		--build-arg NO_PROXY=localhost,127.0.0.1 \
		-t indextts2:latest .

docker-run-indextts2:
	@echo "Starting IndexTTS2 container..."
	cd docker && docker compose -f docker-compose.yml up -d

docker-stop-indextts2:
	@echo "Stopping IndexTTS2 container..."
	cd docker && docker compose -f docker-compose.yml down

docker-logs-indextts2:
	@echo "Showing IndexTTS2 container logs..."
	cd docker && docker compose -f docker-compose.yml logs -f indextts2

docker-shell-indextts2:
	@echo "Entering IndexTTS2 container shell..."
	cd docker && docker compose -f docker-compose.yml exec -it indextts2 bash

.PHONY: start start-dev start-audio-server format lint lint-fix check install-hooks \
	docker-build-indextts2 docker-build-indextts2-proxy docker-run-indextts2 \
	docker-stop-indextts2 docker-logs-indextts2 docker-shell-indextts2
