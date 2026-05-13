---
name: marketpulse-implementation-agent
description: Use when implementing an approved and valid OpenSpec change for MarketPulse. Do not use for spec creation, QA, review, Linear issue creation, or PR creation.
---

# MarketPulse Implementation Skill

## Goal

Implement an approved OpenSpec change for MarketPulse with clean, minimal, testable code.

This skill is for implementation only. It must follow the approved OpenSpec change and must not expand product scope.

## Required Inputs

The user should provide or imply the active change ID.

Example:

```text
Use marketpulse-implementation-agent. Implement add-watchlists-crud.
```

If the active change ID is missing, ask for it.

## Start Gate

Before changing application code, verify all of the following:

- The active OpenSpec change exists under `openspec/changes/<change-id>/`.
- `openspec validate <change-id> --strict` passes.
- The user explicitly approved implementation.
- A Linear issue exists for the change, unless the user explicitly says to skip Linear for this change.

If any condition is missing, stop and report what is missing.

## Required Reading

Before implementation, read:

- `openspec/project.md`
- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- all files under `openspec/changes/<change-id>/specs/**/spec.md`
- relevant existing specs under `openspec/specs/` if they exist
- relevant existing implementation files before editing

## General Implementation Rules

- Follow `tasks.md`.
- Keep changes scoped to the active OpenSpec change.
- Do not add out-of-scope features.
- Do not invent requirements.
- If the spec is unclear, stop and ask for clarification.
- If implementation discoveries change expected behavior, update OpenSpec before or alongside code changes.
- Update implementation and tests together.
- Prefer small, explicit, readable code over clever abstractions.
- Avoid premature abstractions.
- Avoid duplicated business logic.
- Keep modules focused and names clear.
- Do not leave dead code, unused imports, commented-out code, or debug prints.
- Do not log secrets, tokens, provider API keys, database URLs, or credentials.
- Keep error handling explicit and predictable.
- Preserve existing project conventions unless the active change explicitly requires a different approach.

## Backend Architecture Rules

Use FastAPI with a feature-first structure.

FastAPI supports splitting larger applications into multiple files using `APIRouter`. Use that modular approach, but organize MarketPulse backend by feature/capability rather than by global file type.

Default backend structure:

```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      logging.py
      errors.py
    db/
      connection.py
      metadata.py
      migrations/
    features/
      <feature_name>/
        __init__.py
        routes.py
        service.py
        schemas.py
        models.py
        repository.py
        dependencies.py
        exceptions.py
        tests/
          test_<feature_name>_api.py
          test_<feature_name>_service.py
    shared/
      pagination.py
      responses.py
      types.py
```

Feature folder examples:

```text
app/features/auth/
app/features/watchlists/
app/features/market_data/
app/features/news/
app/features/alerts/
app/features/telegram/
app/features/notifications/
app/features/background_jobs/
```

Rules:

- Each feature owns its own `routes.py`, `service.py`, `schemas.py`, `models.py`, and `repository.py` when needed.
- Do not create global `routes/`, `services/`, `schemas/`, or `models/` folders for feature-specific code.
- Use `app/core/` only for cross-cutting application concerns.
- Use `app/db/` only for database connection, metadata, sessions, and migration integration.
- Use `app/shared/` only for reusable helpers that are genuinely shared across features.
- Do not move code into `shared/` until at least two features need it.
- Routes/controllers should be thin.
- Business logic belongs in `service.py`.
- Database access belongs in `repository.py` or clearly isolated data-access functions.
- Pydantic request/response models belong in `schemas.py`.
- SQLAlchemy table definitions belong in `models.py`.
- Feature-specific dependencies belong in `dependencies.py`.
- Feature-specific exceptions belong in `exceptions.py`.
- Backend endpoints must have tests.
- API responses should not expose internal implementation details.

## FastAPI Router Rules

- Every feature with HTTP endpoints should expose an `APIRouter` from `routes.py`.
- Register feature routers in `app/main.py` or a central router registry if one exists.
- Keep route handlers minimal:
   - parse request data
   - call service
   - return response schema
- Do not place business logic inside route handlers.
- Use explicit tags and prefixes.

Example:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/watchlists", tags=["watchlists"])
```

## SQLAlchemy Rules

Use SQLAlchemy Core / SQL Expression Language style for database access.

SQLAlchemy Core is schema-centric and uses SQL expression objects instead of ORM domain objects. SQLAlchemy documents Core as the SQL Expression Language and describes it as separate from ORM usage, with a schema-centric approach.

Rules:

- Prefer SQLAlchemy Core tables, `select()`, `insert()`, `update()`, and `delete()`.
- Avoid SQLAlchemy ORM model classes unless the active OpenSpec change explicitly approves ORM usage.
- Keep table definitions explicit and migration-compatible.
- Use Alembic for schema migrations.
- Do not build SQL with string concatenation.
- Use parameterized SQLAlchemy expressions.
- Keep transaction boundaries explicit.
- Use database constraints for uniqueness and integrity when appropriate.
- Add indexes where the spec or expected query patterns require them.
- Tests must cover database behavior when database logic is added or changed.

Preferred style example:

```python
from sqlalchemy import select

stmt = select(watchlists_table).where(
    watchlists_table.c.user_id == user_id,
    watchlists_table.c.id == watchlist_id,
)
result = await session.execute(stmt)
row = result.mappings().one_or_none()
```

Avoid:

```python
# Avoid unless explicitly approved
session.query(Watchlist).filter(...)
```

## Backend Security Rules

- Validate authentication before accessing user data.
- Never trust `user_id` from request body when authenticated user context exists.
- Always scope user-owned data by authenticated user.
- Validate JWTs according to the auth spec when auth is implemented.
- Do not expose provider API keys to frontend.
- Do not expose database credentials in logs, responses, or health checks.
- Return safe error messages.
- Tests must cover ownership failures when user-owned data is involved.

## Backend Testing Rules

Use Pytest.

When backend is affected, add or update tests for:

- success path
- validation errors
- duplicate/conflict cases when relevant
- authorization or user ownership failures when relevant
- database failure handling when relevant
- external provider failure handling when relevant

Use the existing project test setup. Do not require production services or production credentials.

## Frontend Architecture Rules

Use Next.js 15+ with App Router and TypeScript.

Rules:

- Use TailwindCSS and shadcn/ui for UI.
- Use React Hook Form and Zod for forms and validation.
- Use TanStack Query for server state.
- Use Zustand only for local/client state that is not server state.
- Keep UI components focused and reusable.
- Avoid mixing API calls directly into complex components.
- Every async screen must include loading, error, and empty states.
- Do not hardcode backend response shapes outside generated API types.

## Orval Rules

Use Orval for frontend API client generation from OpenAPI.

Orval generates type-safe TypeScript clients from OpenAPI specifications and supports React Query, Axios/fetch clients, and related frontend integrations.

Rules:

- Do not manually write API client types when they can be generated from OpenAPI.
- Keep OpenAPI contract as the source for generated frontend API clients.
- Use Orval-generated types and hooks/client functions for frontend API calls.
- Add or update Orval config when API client generation is required.
- Do not edit generated Orval output manually.
- If generated files need changes, update the OpenAPI contract or Orval config and regenerate.
- Ensure generated API code is deterministic and reproducible through an npm script.
- Prefer a script such as:

```json
{
	"scripts": {
		"api:generate": "orval --config orval.config.ts"
	}
}
```

Recommended generated client location:

```text
frontend/src/api/generated/
```

Recommended handwritten API wrapper location, if needed:

```text
frontend/src/api/
```

## Frontend Testing and Quality Rules

When frontend is affected:

- run or update typecheck
- run or update lint
- add tests where the project test setup supports them
- verify generated Orval client is up to date when API contracts change

Do not start frontend dev servers unless the user explicitly asks.

## Infrastructure and CI Rules

- Use Docker Compose for local dependencies.
- Use GitHub Actions for CI.
- CI must run backend lint, backend tests, frontend typecheck, and frontend lint.
- CI backend tests must have PostgreSQL service/test database configuration when DB tests are required.
- Use non-production credentials for local and CI environments.
- Prefer deterministic installs:
   - `npm ci` when a package lockfile exists
   - Poetry lockfile-based installs when Poetry is used
- Do not introduce deployment behavior unless the active OpenSpec change explicitly includes deployment.

## External Integration Rules

For external integrations such as Finnhub, Telegram, AWS Cognito, or AWS services:

- Keep secrets server-side.
- Add timeout and failure handling.
- Avoid provider-specific logic leaking into unrelated layers.
- Add tests with mocks/fakes for provider failures.
- Do not call real external services in unit tests.
- Document required environment variables in `.env.example`.

## Allowed Commands

Run only commands needed for implementation and automated verification.

Common backend commands:

```bash
cd backend
poetry run ruff check .
poetry run pytest
```

or, if Poetry is not used:

```bash
cd backend
ruff check .
pytest
```

Common frontend commands:

```bash
cd frontend
npm run lint
npm run typecheck
npm run api:generate
```

Use actual project scripts when they differ.

## Commands to Avoid

Do not run dev servers unless the user explicitly asks:

```bash
uvicorn
fastapi dev
npm run dev
npm start
next dev
next start
```

Do not run destructive commands without explicit user approval:

```bash
docker compose down -v
rm -rf
dropdb
```

## Completion Criteria

Implementation is complete only when:

- OpenSpec validation still passes.
- All relevant tasks in `tasks.md` are completed or explicitly marked as blocked.
- Code changes match the active OpenSpec change.
- Tests are added or updated where required.
- Relevant lint/typecheck/test commands pass, or failures are clearly reported.
- No out-of-scope product features were added.
- No secrets are exposed.
- The change is ready for QA.

## Output Format

Return:

```text
Implementation Result: complete | blocked | needs-spec-update

Files Changed:
- ...

Tasks Completed:
- ...

Tests Added or Updated:
- ...

Validation and Test Results:
- OpenSpec:
- Backend lint:
- Backend tests:
- Frontend lint:
- Frontend typecheck:
- API generation:

Blocked or Unclear Items:
- ...

Commands Run:
- ...

Next Step:
- ready for QA | spec update required | user decision required
```
