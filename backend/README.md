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

## AI Assistant Evals

`tests/ai_eval/` sends scripted English conversations to the assistant running on a real Groq
model and checks which tools it called and with which arguments. Services behind the tools are
in-memory stubs. The run fails when fewer than 90% of scenarios pass. The suite is excluded from
`uv run pytest` and `make test-unit` and never runs without being asked for.

```bash
# Requires GROQ_API_KEY in backend/.env; uses ASSISTANT_EVAL_GROQ_MODEL, falling back to GROQ_MODEL.
docker compose exec -T backend make test-ai-eval
```

Scenarios live in `tests/ai_eval/scenarios.py`; adding one needs no runner changes.

CI runs the suite for pull requests targeting `dev` (job "AI assistant evals"). It needs the
`GROQ_API_KEY` repository secret (Settings → Secrets and variables → Actions). The optional
`ASSISTANT_EVAL_GROQ_MODEL` repository variable selects another model to evaluate. Pull requests
from forks have no access to the secret, so the job fails there with a missing-key message.
