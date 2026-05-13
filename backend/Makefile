.PHONY: sync dev lint test migrate migrate-test

sync:
	uv sync --dev

dev:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest

migrate:
	uv run alembic upgrade head

migrate-test:
	DATABASE_URL=$${TEST_DATABASE_URL} uv run alembic upgrade head
