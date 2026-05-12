SHELL := /bin/sh

.DEFAULT_GOAL := help

.PHONY: help sync dev lint format test test-db migrate revision db-up db-down db-logs check clean

help: ## Show available backend commands.
	@awk 'BEGIN {FS = ":.*##"; printf "Backend commands:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Install backend dependencies, including dev tools.
	uv sync --dev

dev: ## Run the FastAPI backend locally with reload.
	uv run uvicorn app.main:app --reload

lint: ## Run Ruff lint checks.
	uv run ruff check .

format: ## Format backend code with Ruff.
	uv run ruff format .

test: ## Run backend tests that do not require PostgreSQL.
	uv run pytest

test-db: ## Run backend tests, including PostgreSQL connectivity checks.
	RUN_DATABASE_TESTS=true uv run pytest

migrate: ## Apply Alembic migrations to the configured database.
	uv run alembic upgrade head

revision: ## Create an Alembic revision. Usage: make revision MESSAGE="add table"
	@test -n "$(MESSAGE)" || (echo 'Usage: make revision MESSAGE="add table"' && exit 1)
	uv run alembic revision --autogenerate -m "$(MESSAGE)"

db-up: ## Start local PostgreSQL from the repository root Docker Compose file.
	docker compose -f ../docker-compose.yml up -d postgres

db-down: ## Stop local PostgreSQL from the repository root Docker Compose file.
	docker compose -f ../docker-compose.yml down

db-logs: ## Follow local PostgreSQL logs.
	docker compose -f ../docker-compose.yml logs -f postgres

check: lint test ## Run fast backend quality checks.

clean: ## Remove local Python and pytest caches.
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
