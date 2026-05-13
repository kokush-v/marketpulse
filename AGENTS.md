# Agent Instructions

## Project

MarketPulse is built with:

- FastAPI backend
- Next.js frontend
- PostgreSQL database
- Supabase Auth
- OpenSpec for spec-driven development

Agents must follow OpenSpec before implementation work.

## General Agent Rules

- Do not implement code without an approved OpenSpec change.
- Do not invent requirements.
- Do not add out-of-scope functionality.
- Do not read the entire repository unless explicitly required.
- Start from the relevant OpenSpec files.
- Inspect only files related to the selected task.
- Prefer minimal, targeted edits over broad refactoring.
- Do not introduce unrelated abstractions.
- If requirements are unclear or conflicting, stop and ask for clarification.
- Summarize important assumptions before implementation.
- Keep implementation aligned with `tasks.md`.

## Required OpenSpec Reading

Before creating or implementing a change, read:

- `openspec/project.md`
- `openspec/config.yaml`
- relevant current specs in `openspec/specs/`
- relevant change files in `openspec/changes/<change-id>/`

For implementation work, read:

- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- `openspec/changes/<change-id>/specs/**/spec.md`

## OpenSpec Workflow

Before implementation, validate the change:

```bash
openspec validate <change-id> --strict
```

During implementation:

- Follow `tasks.md` in order.
- Do not mark a task complete until the related code and tests are done.
- Do not change approved requirements without explicit clarification.
- If implementation discoveries conflict with the approved spec, stop and ask.

After implementation:

```bash
openspec validate <change-id> --strict
```

Run relevant tests and linters before considering the work complete.

## OpenSpec Task Modes

When the user asks to create, update, or review an OpenSpec proposal, operate in proposal mode.

Proposal mode rules:

- Create or update only OpenSpec files.
- Do not implement application code.
- Produce `proposal.md`, `tasks.md`, optional `design.md`, and spec delta files.
- Validate with `openspec validate <change-id> --strict`.
- Stop after the OpenSpec change is valid.
- If the user request is vague, ask clarification questions before creating OpenSpec files.
- Do not force the user to provide a detailed prompt.
- Convert short user intent into a structured OpenSpec change through clarification.
- Ask only scope-changing questions.
- After clarification, summarize the agreed scope before writing files.

When the user asks to implement an approved OpenSpec change, operate in implementation mode.

Implementation mode rules:

- Validate the change before editing application code.
- Read only the approved change files and directly relevant code.
- Follow `tasks.md`.
- Do not add out-of-scope behavior.
- Update tests together with implementation.
- Validate OpenSpec again after implementation.

## Backend Architecture

Use feature-based FastAPI structure:

```text
app/
  features/
    <feature_name>/
      routes.py
      service.py
      schemas.py
      models.py
      dependencies.py
      repository.py
tests/
```

File responsibilities:

- `routes.py` defines HTTP endpoints only.
- `service.py` contains business logic.
- `repository.py` contains database access when queries become non-trivial.
- `schemas.py` contains Pydantic request and response schemas.
- `models.py` contains SQLAlchemy models.
- `dependencies.py` contains feature-specific FastAPI dependencies.

Tests

- `tests/` should mirror the feature structure for test organization.

## Backend Code Style

- Write simple, explicit code.
- Prefer readability over clever abstractions.
- Use typed function signatures.
- Keep routes thin.
- Keep business logic in services.
- Keep database access in repositories when queries become non-trivial.
- Use explicit Pydantic request and response schemas.
- Avoid global mutable state.
- Avoid hidden side effects in helper functions.
- Avoid broad refactoring unless required by the OpenSpec change.
- Do not place business logic in route handlers.
- Do not place complex database queries directly in route handlers.
- Do not silently swallow exceptions.
- Prefer domain-specific exceptions where useful.
- Keep API responses stable and documented through OpenAPI.

## Async Backend Rules

- Prefer async libraries for all database, network, Telegram, and external provider I/O.
- Use SQLAlchemy `AsyncSession` for application database access.
- Use `asyncpg` as the PostgreSQL async driver.
- Do not share one `AsyncSession` across concurrent tasks.
- Do not call blocking SDK methods inside async route handlers, services, Telegram handlers, or background jobs.
- Prefer official async SDKs where available.
- Use async HTTP clients only behind provider adapters when no suitable async SDK exists.
- Keep external provider clients isolated behind service or provider interfaces.
- Do not mix sync and async database sessions in application code.
- Do not use blocking file, network, or sleep operations inside async code.

## Backend Libraries

Preferred backend libraries:

- FastAPI for backend API
- SQLAlchemy async ORM for database access
- asyncpg as PostgreSQL driver
- Alembic for migrations
- Pydantic for schemas and validation
- Pytest for tests
- pytest-asyncio for async tests
- Ruff for linting and formatting
- Supabase Auth for authentication
- Supabase async Python client when server-side Supabase API access is needed
- PyJWT or python-jose for local JWT verification
- aiogram for async Telegram Bot API integration
- HTTPX only as a fallback for async external API calls when no suitable async SDK exists

## Authentication Rules

- Supabase Auth is the authentication provider.
- Protected backend endpoints must validate Supabase access tokens.
- Derive the current user from the validated JWT and the local `users` record.
- Do not trust user IDs from request bodies, query parameters, or path parameters when ownership can be derived from the authenticated user.
- Enforce row ownership in database queries, not only at the route layer.
- Keep auth-specific code isolated in an `auth` feature or shared security module.
- Do not expose provider secrets or service-role keys to the frontend.

## External Integration Rules

- Prefer official async SDKs or stable async client libraries.
- If a provider only offers a sync SDK, do not call it directly from async application code.
- Wrap provider access in a dedicated provider class or service.
- Handle provider failures, timeouts, rate limits, malformed responses, and missing fields.
- Normalize external data before persistence.
- Keep provider API keys on the backend only.

## Telegram Rules

- Use aiogram for Telegram Bot API integration.
- Keep Telegram handlers asynchronous.
- Keep Telegram command handlers thin.
- Put Telegram business logic in services.
- Use background jobs for scheduled digests and alert delivery when needed.
- Do not block the event loop from Telegram handlers.
- Make notification delivery idempotent where practical.

## Database Rules

- Use SQLAlchemy models for database tables.
- Use Alembic migrations for schema changes.
- Do not change models without adding or updating migrations.
- Keep ownership constraints explicit in queries.
- Prevent duplicate user-owned resources where required by the spec.
- Normalize stock tickers to uppercase before persistence and comparison.
- Use explicit enums for alert rule types.

## Frontend Architecture

Use Next.js App Router patterns.

Recommended organization:

```text
app/
  (auth)/
  (dashboard)/
features/
  <feature_name>/
    components/
    hooks/
    schemas/
    utils/
shared/
  components/
  lib/
  types/
```

## Frontend Code Style

- Use TypeScript.
- Use shadcn/ui for base components.
- Use TailwindCSS for styling.
- Use TanStack Query for server state.
- Use Zustand only when client-side state is actually needed.
- Use React Hook Form and Zod for forms.
- Keep page components focused on composition.
- Move reusable UI logic into hooks or small components.
- Show clear loading, empty, and error states for every async screen.
- Do not manually duplicate generated API request and response types when Orval can generate them.
- Avoid large components with mixed fetching, validation, and presentation logic.

## API Client Generation

- Backend OpenAPI output is the source of truth for frontend API clients.
- Use Orval to generate TypeScript API clients from the FastAPI OpenAPI schema.
- Prefer generated React Query hooks for standard CRUD and read flows.
- Use custom frontend API code only when generated clients are not practical.
- When an endpoint contract changes:
   - update backend schemas
   - regenerate the frontend client
   - update affected UI code
   - update tests if needed

## Testing Rules

Backend:

- Add or update Pytest coverage for changed backend behavior.
- Use `pytest-asyncio` for async behavior.
- Test ownership and authorization checks for user-owned resources.
- Test provider error handling where relevant.
- Test duplicate prevention where required by the spec.

Frontend:

- Add tests for important form validation and user flows when practical.
- Cover loading, empty, and error states for new async screens.
- Ensure generated API types remain aligned with backend changes.

## Quality Gates

Run relevant commands before marking work complete.

Backend examples:

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
```

OpenSpec:

```bash
openspec validate <change-id> --strict
```

Frontend examples:

```bash
npm run lint
npm run typecheck
npm run test
```

Use the existing project scripts if they differ from these examples.

## Things To Avoid

- Do not implement features directly from vague user requests without an OpenSpec change.
- Do not expand scope beyond the approved change.
- Do not add speculative abstractions.
- Do not read unrelated modules just to infer hidden requirements.
- Do not mix sync database access into async backend code.
- Do not call blocking SDKs from async handlers.
- Do not put provider credentials in frontend code.
- Do not manually duplicate OpenAPI-generated frontend types.
- Do not mark OpenSpec tasks complete before code and tests are actually done.
