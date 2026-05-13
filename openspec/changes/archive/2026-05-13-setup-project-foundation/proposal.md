## Summary
Initialize the MarketPulse project foundation across backend, frontend, infrastructure, and quality tooling so implementation changes can proceed on a consistent baseline.

## Problem
The repository currently lacks initialized backend and frontend application structure and does not yet provide the agreed local/runtime quality baseline. This blocks implementation of approved feature changes such as authentication.

## Proposed Solution
Establish a complete project foundation that includes:
- backend skeleton (FastAPI, async SQLAlchemy, Alembic)
- frontend skeleton (Next.js App Router, TailwindCSS, shadcn/ui setup, TanStack Query, Orval configuration)
- docker-compose with separate PostgreSQL services for development and tests
- CI quality checks and local lint/test scripts
- backend unit-test baseline using mocks only

## Scope
In scope:
- Create backend and frontend starter architecture and baseline configuration
- Configure development and test PostgreSQL services in Docker Compose
- Define CI jobs for linting and required checks
- Add backend linting and unit test setup
- Add frontend lint/typecheck/build baseline checks
- Add Orval configuration for future API client generation

## Non-Goals
- Implementing authentication business logic or product features
- Adding integration tests or end-to-end tests
- Adding frontend test suites in this change
- Creating production infrastructure deployment workflows beyond baseline CI checks

## Impact
Affected domains:
- `api-client-generation`

Primary workflows:
- Local development bootstrap
- Automated quality checks in CI
- Backend unit testing with mock-based isolation
- Frontend readiness for generated API client integration

System impact:
- Provides a stable baseline required by future feature implementation changes.
