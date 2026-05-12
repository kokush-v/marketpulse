# Design: Setup Project Foundation

## Overview

This change establishes the repository foundation for MarketPulse without adding product features. It creates the minimal backend, frontend, local database, migration, quality, and CI structure needed before feature-specific changes begin.

The backend foundation centers on FastAPI, SQLAlchemy database connectivity, Alembic migrations, Pytest, and Ruff. The frontend foundation centers on Next.js with TypeScript and linting. Local infrastructure centers on Docker Compose for PostgreSQL, including an isolated test PostgreSQL service for deterministic database checks. CI verifies the same foundation checks expected during local development.

## Data Model Changes

No product domain tables are introduced by this change.

Alembic SHALL be configured so later changes can add database schema migrations. If an initial baseline migration is needed for tooling verification, it SHALL avoid introducing watchlists, market data, alerts, Telegram, authentication, or notification domain tables.

## API Changes

The backend SHALL expose a health check endpoint for foundation verification.

The health check endpoint SHALL verify backend service availability and database connectivity. It SHALL return controlled status information and SHALL NOT expose database credentials, connection strings, stack traces, or other secrets.

No product API endpoints are introduced by this change.

## Background Job Changes

No background jobs are introduced by this change.

## Security Considerations

This change does not introduce Cognito authentication or user-owned resources.

Local configuration SHALL keep database credentials and connection strings out of frontend code. Backend and frontend environment examples SHALL be separated so frontend configuration contains only public client-side values. Backend logs and API responses SHALL NOT expose secrets. CI configuration SHALL use non-production test or local-only values for foundation checks.

## Failure Handling

Backend startup and health checks SHOULD fail clearly when required configuration is missing or PostgreSQL is unavailable.

Database connectivity failures SHALL be handled without leaking credentials. CI backend tests SHALL run with a PostgreSQL service or equivalent test database configuration. Local database smoke checks SHOULD use the isolated test PostgreSQL service and `TEST_DATABASE_URL` when available, falling back to `DATABASE_URL` only when a dedicated test URL is not configured. CI failures SHALL make it clear which foundation check failed: backend lint, backend tests, frontend typecheck, or frontend lint.

## Open Questions

- None.
