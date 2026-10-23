# MarketPulse — Claude Code Instructions

`AGENTS.md` is the single source of project rules shared by Codex, GitHub Copilot, and Claude Code.
Follow it fully; it is imported below. Do not duplicate or override its rules here — this file only
adds Claude Code–specific notes and a quick project map.

@AGENTS.md

## Skills (shared with Codex and Copilot)

The single source of project skills is `.agents/skills/<name>/SKILL.md`.
Codex and GitHub Copilot read `.agents/skills/` natively; Claude Code reads only `.claude/skills/`,
so `.claude/skills/<name>` is a symlink to it. Edit skills only in `.agents/skills/`; when adding a
new skill, create its Claude Code symlink (`ln -s ../../.agents/skills/<name> .claude/skills/<name>`).

Default delivery flow:

```text
/create-spec -> /create-linear-task -> /implement-spec -> /test-spec -> /create-pr
```

- `create-spec` — proposal mode: create/update an OpenSpec change only, no app code.
- `create-linear-task` — Linear issue from an OpenSpec change (uses the `linear` MCP server from `.mcp.json`; falls back to Markdown output).
- `implement-spec` — implementation mode for an approved, valid change.
- `test-spec` — verify implementation against spec and tasks, report gaps.
- `create-pr` — focused PR via `gh`, linked to the OpenSpec change and Linear issue.
- `fix-pr-comments` — resolve unresolved PR review threads one by one via `gh api graphql`.

When a skill suggests host commands like `cd backend && make lint` or `npm run lint`, run the
container equivalents below instead (see "Containerized Development" in `AGENTS.md`).

## Repository Map

- `backend/` — FastAPI (Python 3.12, uv). Features in `app/features/<feature>/`
  (`ai_assistant`, `alerts`, `auth`, `background_jobs`, `market_data`, `news`, `notifications`,
  `system`, `telegram`, `watchlists`). Config in `app/core/config.py`, DB in `app/db/`,
  migrations in `alembic/`. Tests in `tests/unit/features/<feature>/` and `tests/features/`.
  AI assistant uses LangGraph + `langchain-groq`.
- `frontend/` — Next.js 15 App Router (React 19). Routes in `app/(auth)` and `app/(dashboard)`,
  features in `features/<feature>/`, shared code in `shared/`. Orval output in
  `src/api/generated/` (git-ignored, regenerate it), custom fetch mutator in `src/api/http-client.ts`.
  Tests: Jest + Testing Library.
- `market-data-api/` — Rails API-only service (CoinGecko, NewsAPI) with Redis caching,
  port 3001. Backend calls it via `MARKET_DATA_API_BASE_URL`.
- `backend-cron` service — runs `app.features.background_jobs.cron_runtime`.
- `openspec/` — `project.md`, `config.yaml`, current specs in `specs/<domain>/`, changes in
  `changes/<change-id>/`, completed ones in `changes/archive/`.
- `k8s/` — Kustomize manifests and scripts for local Kubernetes; secrets are never committed.
- `market-pulse.md` — original technical task (historical; OpenSpec specs take precedence).

## Commands

Start the stack first: `docker compose up --build` (needs `backend/.env`, `frontend/.env`,
`market-data-api/.env` copied from `.env.example`).

```bash
# OpenSpec (host CLI)
openspec list
openspec validate <change-id> --strict

# Backend
docker compose exec -T backend uv run ruff check .
docker compose exec -T backend uv run ruff format --check .
docker compose exec -T backend uv run pytest tests/unit
docker compose exec -T backend uv run pytest tests/unit/features/<feature> -k <name>
docker compose exec -T backend uv run alembic revision --autogenerate -m "<message>"
docker compose exec -T backend uv run alembic upgrade head

# Frontend
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run test -- --runInBand
docker compose exec -T frontend npm run build

# Regenerate the Orval client after a backend contract change
# (inside the container the backend is reachable as `backend`, not `localhost`)
docker compose exec -T -e MARKETPULSE_OPENAPI_URL=http://backend:8000/openapi.json frontend npm run generate:api

# Market-data API
docker compose exec -T market-data-api bundle exec rails test
```

CI (`.github/workflows/ci.yml`) runs backend `make lint` + `make test-unit`, then exports the
OpenAPI schema, regenerates the Orval client, and runs frontend lint, typecheck, tests, and build.
The Husky pre-commit hook runs backend Ruff and frontend lint inside the containers.

## Claude Code Notes

- Never read or print `.env` files or `k8s/secrets/`; use the `.env.example` files for variable names.
- Use `gh` for GitHub operations (PRs, review threads).
- If the Docker stack is not running, say so instead of falling back to host commands.
