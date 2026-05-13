# project-foundation Specification

## Purpose
Define the baseline local development foundation for MarketPulse, including runnable backend and frontend applications, local PostgreSQL services, and separated environment examples.
## Requirements
### Requirement: Backend application can run locally

The system SHALL provide a FastAPI backend application that can be started in a local development environment.

#### Scenario: Start backend locally

- Given the backend dependencies are installed
- And required local environment values are configured
- When the developer starts the backend application
- Then the FastAPI service is available locally
- And the service exposes generated API documentation through FastAPI's standard documentation endpoints

### Requirement: Frontend application can run locally

The system SHALL provide a Next.js frontend application that can be started in a local development environment.

#### Scenario: Start frontend locally

- Given the frontend dependencies are installed
- When the developer starts the frontend application
- Then the Next.js service is available locally
- And the application can render its initial route without requiring product feature data

### Requirement: Local PostgreSQL is available through Docker Compose

The system SHALL provide Docker Compose configuration for running PostgreSQL locally.

The system SHALL provide a separate PostgreSQL service for local test database checks through a Docker Compose test profile.

#### Scenario: Start local PostgreSQL

- Given Docker is available on the developer machine
- When the developer starts the Docker Compose database service
- Then PostgreSQL starts locally
- And the configured database, username, and password are available to the backend

#### Scenario: Start local test PostgreSQL

- Given Docker is available on the developer machine
- When the developer starts the Docker Compose test database profile
- Then PostgreSQL starts locally for tests on a port separate from the development database
- And the configured test database, username, and password are available to backend tests

### Requirement: Local environment examples are separated by runtime

The system SHALL provide separate backend and frontend local environment example files.

The frontend local environment example SHALL NOT include backend-only database connection strings or provider secrets.

#### Scenario: Configure local runtime environment files

- Given the repository has local environment examples
- When a developer prepares local configuration
- Then Docker Compose database values are copied from the root environment example
- And backend application values are copied from the backend environment example
- And frontend public client values are copied from the frontend environment example

### Requirement: Backend can connect to PostgreSQL

The backend SHALL use configured database connection settings to connect to local PostgreSQL.

#### Scenario: Backend verifies database connectivity

- Given PostgreSQL is running through Docker Compose
- And the backend database connection settings match the local PostgreSQL service
- When the backend performs a database connectivity check
- Then the connection succeeds

#### Scenario: Backend verifies test database connectivity

- Given test PostgreSQL is running through Docker Compose
- And `TEST_DATABASE_URL` matches the local test PostgreSQL service
- When backend database smoke tests run
- Then the smoke tests connect to the test database instead of the development database

#### Scenario: Backend database smoke tests fall back to default database URL

- Given `TEST_DATABASE_URL` is not configured
- And `DATABASE_URL` is configured
- When backend database smoke tests run
- Then the smoke tests use `DATABASE_URL`

#### Scenario: Backend reports database connectivity failure

- Given PostgreSQL is unavailable or the backend database connection settings are invalid
- When the backend performs a database connectivity check
- Then the connection failure is surfaced in a controlled way
- And the backend does not expose database credentials in logs or responses

### Requirement: Alembic is configured for migrations

The backend SHALL include Alembic configuration for managing PostgreSQL schema migrations.

#### Scenario: Run Alembic commands locally

- Given the backend dependencies are installed
- And PostgreSQL is running locally
- When the developer runs Alembic migration commands
- Then Alembic can locate the backend migration configuration
- And Alembic can connect to the configured PostgreSQL database

### Requirement: Health check endpoint works

The backend SHALL expose a health check endpoint for local and CI verification.

The health check endpoint SHALL verify database connectivity as part of its health status.

#### Scenario: Health check succeeds

- Given the backend is running
- And PostgreSQL connectivity is available
- When a client requests the health check endpoint
- Then the backend returns a successful response
- And the response includes service and database status information

#### Scenario: Health check handles dependency failure

- Given the backend is running
- And PostgreSQL connectivity is unavailable
- When a client requests the health check endpoint
- Then the backend returns a controlled unhealthy response
- And the response does not expose secrets or internal connection strings

### Requirement: Backend quality tools are configured

The backend SHALL include Pytest and Ruff configuration.

#### Scenario: Run backend tests

- Given backend dependencies are installed
- When the developer runs Pytest
- Then the backend test suite completes successfully

#### Scenario: Run backend lint checks

- Given backend dependencies are installed
- When the developer runs Ruff
- Then Ruff completes successfully

### Requirement: Frontend quality tools are configured

The frontend SHALL include TypeScript and lint checks.

#### Scenario: Run frontend typecheck

- Given frontend dependencies are installed
- When the developer runs the frontend typecheck command
- Then TypeScript validation completes successfully

#### Scenario: Run frontend lint

- Given frontend dependencies are installed
- When the developer runs the frontend lint command
- Then frontend linting completes successfully

### Requirement: CI verifies the foundation

The repository SHALL include a GitHub Actions workflow for foundation checks.

CI backend tests SHALL run with PostgreSQL available through a CI service container or equivalent test database configuration.

#### Scenario: CI runs on proposed changes

- Given a pull request or configured branch event triggers CI
- When the GitHub Actions workflow runs
- Then CI runs backend Ruff checks
- And CI runs backend Pytest tests
- And CI runs frontend typecheck
- And CI runs frontend lint

#### Scenario: CI provides PostgreSQL for backend tests

- Given the GitHub Actions workflow runs backend tests
- When the backend test job starts
- Then PostgreSQL is available to the backend tests
- And the backend test environment uses non-production database credentials
