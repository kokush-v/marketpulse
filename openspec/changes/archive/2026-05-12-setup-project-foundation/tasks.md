# Tasks

## Backend

- [x] Create the FastAPI backend project structure.
- [x] Add configuration loading for local environment values, including the PostgreSQL connection string.
- [x] Split local environment examples into backend and frontend runtime files.
- [x] Add database session and connectivity setup for PostgreSQL.
- [x] Add a health check endpoint that reports service availability and database connectivity.
- [x] Add local backend startup documentation or scripts consistent with the repository conventions.

## Frontend

- [x] Create the Next.js frontend project structure using the App Router.
- [x] Configure TypeScript and linting for the frontend.
- [x] Add local frontend startup documentation or scripts consistent with the repository conventions.

## Database

- [x] Add Docker Compose configuration for local PostgreSQL.
- [x] Add Docker Compose configuration for isolated local test PostgreSQL.
- [x] Add environment configuration for local PostgreSQL credentials and database name.
- [x] Add environment configuration for local test PostgreSQL credentials and database name.
- [x] Configure Alembic for migration generation and execution.
- [x] Add an initial Alembic baseline that does not introduce product domain tables unless required by the migration tooling.

## Infra

- [x] Add GitHub Actions CI workflow.
- [x] Configure CI PostgreSQL service and database environment for backend tests.
- [x] Configure CI to run backend Ruff checks.
- [x] Configure CI to run backend Pytest tests.
- [x] Configure CI to run frontend typecheck.
- [x] Configure CI to run frontend lint.

## Tests

- [x] Add Pytest configuration.
- [x] Add backend tests for the health check endpoint.
- [x] Add backend tests or smoke checks for database connectivity.
- [x] Configure database smoke checks to prefer `TEST_DATABASE_URL` and fall back to `DATABASE_URL`.
- [x] Verify Ruff runs successfully.
- [x] Verify frontend typecheck runs successfully.
- [x] Verify frontend lint runs successfully.
