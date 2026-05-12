# Proposal: Setup Project Foundation

## Problem

MarketPulse needs a base technical foundation before feature implementation starts. The repository does not yet define the backend, frontend, local database, migration, quality, or CI structure required for later product work.

## Scope

- Set up a FastAPI backend application that can start locally.
- Set up a Next.js frontend application that can start locally.
- Provide Docker Compose configuration for local PostgreSQL.
- Provide a separate Docker Compose PostgreSQL service for local test database checks.
- Configure backend database connectivity to local PostgreSQL.
- Configure Alembic for database migrations.
- Add a backend health check endpoint.
- Configure Pytest for backend tests.
- Configure Ruff for backend linting and formatting checks.
- Add basic GitHub Actions CI for backend lint, backend tests, frontend typecheck, and frontend lint.

## Out of Scope

- Cognito authentication.
- Watchlists CRUD.
- Market data integration.
- Telegram integration.
- Alerts.
- AWS deployment.
- Product application behavior beyond foundation-level startup, health, database connectivity, migrations, linting, tests, and CI.

## Acceptance Criteria

- Backend starts locally.
- Frontend starts locally.
- PostgreSQL runs locally through Docker Compose.
- An isolated test PostgreSQL database can run locally through a Docker Compose test profile.
- Backend can connect to PostgreSQL.
- Alembic is configured.
- Health check endpoint works.
- Pytest runs successfully.
- Ruff runs successfully.
- CI runs backend lint, backend tests, frontend typecheck, and frontend lint.

## Related Specs

- None yet. This is the first OpenSpec change.
