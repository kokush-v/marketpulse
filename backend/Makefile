.PHONY: sync dev lint test test-unit test-ai-eval migrate migrate-test

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

# Calls the real Groq model; requires GROQ_API_KEY.
test-ai-eval:
	uv run pytest tests/ai_eval -s

migrate:
	uv run alembic upgrade head

migrate-test:
	DATABASE_URL=$$(uv run python -c "from app.core.config import settings; print(settings.test_database_url)") uv run alembic upgrade head
