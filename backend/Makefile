.PHONY: sync dev lint test test-unit migrate migrate-test

sync:
	uv sync --dev

dev:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

migrate:
	uv run alembic upgrade head

migrate-test:
	DATABASE_URL=$$(uv run python -c "from app.core.config import settings; print(settings.test_database_url)") uv run alembic upgrade head
