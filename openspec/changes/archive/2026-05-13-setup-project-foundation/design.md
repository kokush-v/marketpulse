## Overview
This change establishes the technical baseline for MarketPulse development with explicit separation of development and test database runtimes, standardized quality gates, and scaffolded backend/frontend architecture.

## Architectural Decisions

### 1. Backend Foundation
- Backend uses FastAPI as API framework.
- Database integration uses SQLAlchemy async ORM with `asyncpg`.
- Alembic is the migration system baseline.
- Initial backend structure follows feature-based layout conventions.

### 2. Frontend Foundation
- Frontend uses Next.js App Router with TypeScript.
- TailwindCSS and shadcn/ui are configured as UI baseline.
- TanStack Query is configured for server-state baseline.
- Orval configuration is added to enable typed API client generation from backend OpenAPI.

### 3. Database Runtime Separation
- Docker Compose includes two PostgreSQL services:
  - development database on port `5432`
  - test database on port `5433`
- This separation prevents test execution from mutating development data.

### 4. Testing Strategy at Foundation Stage
- Backend tests are limited to unit tests with mocks.
- Integration and E2E tests are explicitly out of scope for this change.
- Frontend test suites are out of scope for this change.

### 5. CI and Quality Gates
- CI runs baseline lint and verification commands for backend and frontend.
- Backend quality checks include lint and unit tests.
- Frontend quality checks include lint, typecheck, and build validation.

## Risks and Mitigations
- Risk: mismatch between local scripts and CI commands can cause non-reproducible failures.
- Mitigation: ensure CI uses the same project scripts/targets documented for local usage.

- Risk: accidental connection to wrong database in tests.
- Mitigation: enforce dedicated test DB service and explicit test database DSN configuration.

## Rollback Considerations
- Foundation components can be rolled back by reverting scaffold/config changes together to preserve consistency between scripts, CI, and runtime environment.
