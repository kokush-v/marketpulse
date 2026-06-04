# Backend

## Setup

```bash
uv sync --dev
```

## Development

```bash
uv run uvicorn app.main:app --reload
```

Run the cron scheduler locally:

```bash
uv run python -m app.features.background_jobs.cron_runtime
```

Cron container files live in `docker/cron/`.

## Quality

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```
