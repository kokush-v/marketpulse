---
name: marketpulse-qa-agent
description: Use after implementation to verify an OpenSpec change through tests, linting, type checks, and acceptance criteria review. Do not run development servers.
---

# MarketPulse QA Skill

## Goal

Verify that the implemented code satisfies the active OpenSpec change using automated checks only.

This skill is for QA validation after implementation. It must not start development servers or manually run the application.

## When to Use

Use this skill after:

- an OpenSpec change was implemented
- implementation tests were added or updated
- the user asks to verify readiness before review

Example:

```text
Use marketpulse-qa-agent. Test add-watchlists-crud.
```

If the active change ID is missing, ask for it.

## Required Reading

Before testing, read:

- `openspec/project.md`
- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- all files under `openspec/changes/<change-id>/specs/**/spec.md`
- relevant existing specs under `openspec/specs/` if they exist
- current `git diff`

## Hard Limits

Do not run:

```bash
uvicorn
fastapi dev
npm run dev
npm start
next dev
next start
docker compose up
docker compose up -d
```

Do not manually start backend, frontend, bot, or background worker services.

Do not open browser-based checks unless the user explicitly asks.

Do not run destructive commands such as:

```bash
docker compose down -v
rm -rf
dropdb
```

unless the user explicitly approves.

## Validation Rules

First run:

```bash
openspec validate <change-id> --strict
```

If OpenSpec validation fails:

- stop
- report the validation error
- do not continue QA until the spec is fixed

## Allowed Commands

Use only commands needed for automated verification.

Backend, if affected:

```bash
cd backend
ruff check .
pytest
```

If the backend uses Poetry:

```bash
cd backend
poetry run ruff check .
poetry run pytest
```

Frontend, if affected:

```bash
cd frontend
npm run lint
npm run typecheck
```

If package scripts differ, inspect `package.json` and use the available lint/typecheck/test scripts.

Repository-level checks, if available:

```bash
git diff --check
```

Docker is allowed only for test dependencies when required by the test setup, not for starting dev services.

Allowed Docker examples:

```bash
docker compose up -d postgres-test
docker compose ps
```

Only use these if backend tests require PostgreSQL and no test database is already available.

## QA Checklist

Check:

- OpenSpec validation passes
- every acceptance criterion from `proposal.md`
- every task from `tasks.md`
- every requirement and scenario from nested `spec.md`
- implementation stays within scope
- no out-of-scope product features were added
- tests cover the implemented behavior
- lint/typecheck/test commands pass
- CI configuration matches the change
- no secrets, tokens, provider API keys, or database credentials are exposed

## Backend Checks

When backend is affected, verify:

- `pytest` passes
- `ruff check .` passes
- API behavior is covered by tests
- validation errors are covered when relevant
- database migrations exist when schema changes are made
- auth and user ownership are tested when relevant
- external provider failures are tested when relevant
- database failures are tested when relevant
- secrets are not logged or returned

Do not start the backend server for QA.

## Frontend Checks

When frontend is affected, verify:

- lint passes
- typecheck passes
- test script passes if available
- forms and validation logic are tested when relevant
- API client behavior matches the API contract
- async screens include loading, error, and empty states when UI screens are added or changed

Do not start the frontend dev server for QA.

## Database and Test Dependencies

When tests require PostgreSQL:

- prefer the existing test setup
- use test-only database credentials
- do not use production credentials
- do not require persistent test database state
- do not start the full app stack

If the test database is missing and tests cannot run, report QA as blocked and explain what is missing.

## CI Checks

When CI is affected, verify:

- workflow files exist
- backend lint/test jobs are present
- frontend lint/typecheck jobs are present
- PostgreSQL service is configured when backend tests require it
- CI uses deterministic install commands where applicable, such as `npm ci` when a lockfile exists
- CI does not use production secrets for tests

## Test Coverage Expectations

For each implemented change, check whether tests cover relevant cases:

- success path
- invalid input
- authorization failure
- user ownership failure
- duplicate/conflict cases
- database failure
- external provider failure
- retry or idempotency behavior

Do not require irrelevant tests.

## Allowed File Changes

Allowed:

- add or update tests required by the active OpenSpec change
- make minimal test configuration fixes
- update QA-related documentation if needed

Not allowed:

- add product features
- change feature behavior without updating OpenSpec
- widen scope
- archive the change
- create Linear issues
- create pull requests
- merge branches

## Output Format

Return:

```text
QA Result: pass | fail | blocked

Validation:
- OpenSpec:
- Backend tests:
- Backend lint:
- Frontend typecheck:
- Frontend lint:
- CI:
- Git diff check:

Acceptance Criteria:
- Passed:
- Failed:
- Not verified:

Missing Tests:
- ...

Out-of-scope Changes:
- ...

Files Changed:
- ...

Blocked Items:
- ...

Recommendation:
- ready for review | fix required | spec update required
```

## Stop Conditions

Stop and report `blocked` if:

- active change ID is missing
- OpenSpec validation fails
- required test environment is unavailable
- test database is missing and required
- required scripts are missing from the project
- implementation differs from the spec
- acceptance criteria are ambiguous

Do not bypass these conditions by starting development servers.
