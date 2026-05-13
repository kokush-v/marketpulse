# Backend

## Setup

```bash
uv sync --dev
```

## Development

```bash
uv run uvicorn app.main:app --reload
```

## Quality

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```
