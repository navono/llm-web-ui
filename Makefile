install:
	uv sync --all-extras
	$(MAKE) install-hooks

start:
	uv run -m src.main run

start-dev:
	@chmod +x scripts/dev-server.sh
	uv run watchfiles --ignore-paths "./src/__pycache__" --sigint-timeout 5 --sigkill-timeout 10 "bash scripts/dev-server.sh" "./src"

# Docker targets for API Gateway
docker-up:
	@echo "Starting all services with API Gateway..."
	@docker compose --env-file .env -f docker/docker-compose.yml up -d

docker-down:
	@echo "Stopping all services..."
	@docker compose --env-file .env -f docker/docker-compose.yml down

docker-restart:
	@echo "Restarting all services..."
	@docker compose --env-file .env -f docker/docker-compose.yml restart

docker-logs:
	@echo "Showing all service logs..."
	@docker compose --env-file .env -f docker/docker-compose.yml logs -f

docker-logs-nginx:
	@echo "Showing nginx logs..."
	@docker compose --env-file .env -f docker/docker-compose.yml logs -f nginx

docker-logs-vtuber:
	@echo "Showing open-llm-vtuber logs..."
	@docker compose --env-file .env -f docker/docker-compose.yml logs -f open-llm-vtuber

docker-test:
	@echo "Testing services..."
	@docker compose --env-file .env -f docker/docker-compose.yml exec nginx curl -f http://localhost || exit 1

docker-ps:
	@echo "Showing running containers..."
	@docker compose --env-file .env -f docker/docker-compose.yml ps

docker-build-all:
	@echo "Building all Docker images..."
	@docker compose --env-file .env -f docker/docker-compose.yml build

format:
	uv run ruff format .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix . --unsafe-fixes

check:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest tests/ -v

test-book-speech:
	uv run pytest tests/test_book_speech.py -v

test-book-speech-manual:
	uv run python tests/test_book_speech_manual.py

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
	@export $$(cat .env | grep -v '^#' | xargs) && docker build -f docker/Dockerfile.indextts2 \
		--build-arg HTTP_PROXY=$$PROXY_SERVER \
		--build-arg HTTPS_PROXY=$$PROXY_SERVER \
		--build-arg NO_PROXY=$$NO_PROXY \
		-t indextts2:latest .

docker-run-indextts2:
	@echo "Starting IndexTTS2 container..."
	@docker compose --env-file .env -f docker/docker-compose.yml up -d indextts2

docker-stop-indextts2:
	@echo "Stopping IndexTTS2 container..."
	@docker compose --env-file .env -f docker/docker-compose.yml down indextts2

docker-logs-indextts2:
	@echo "Showing IndexTTS2 container logs..."
	@docker compose --env-file .env -f docker/docker-compose.yml logs -f indextts2

docker-shell-indextts2:
	@echo "Entering IndexTTS2 container shell..."
	@docker compose --env-file .env -f docker/docker-compose.yml exec -it indextts2 bash

docker-run-vtuber:
	@echo "Starting Open-LLM-VTuber container..."
	@docker compose --env-file .env -f docker/docker-compose.yml up -d open-llm-vtuber

docker-stop-vtuber:
	@echo "Stopping Open-LLM-VTuber container..."
	@docker compose --env-file .env -f docker/docker-compose.yml down open-llm-vtuber


.PHONY: start start-dev start-audio-server format lint lint-fix check test test-book-speech test-book-speech-manual install-hooks \
	docker-build-indextts2 docker-build-indextts2-proxy docker-run-indextts2 \
	docker-stop-indextts2 docker-logs-indextts2 docker-shell-indextts2 \
	docker-up docker-down docker-restart docker-logs docker-logs-nginx docker-logs-vtuber \
	docker-test docker-ps docker-build-all
