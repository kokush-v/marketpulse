## 1. Backend scaffold
- [x] 1.1 Create backend project baseline with FastAPI application entrypoint and health endpoint.
- [x] 1.2 Configure async SQLAlchemy session setup using `asyncpg`.
- [x] 1.3 Initialize Alembic baseline wiring for async SQLAlchemy models.
- [x] 1.4 Add backend lint/format configuration and runnable project scripts/targets.

## 2. Frontend scaffold
- [x] 2.1 Create Next.js App Router baseline with TypeScript.
- [x] 2.2 Configure TailwindCSS and shadcn/ui baseline setup.
- [x] 2.3 Configure TanStack Query provider baseline for app routing tree.
- [x] 2.4 Add Orval configuration for generating frontend API clients from backend OpenAPI.
- [x] 2.5 Add frontend runnable scripts for lint, typecheck, and build.

## 3. Infrastructure baseline
- [x] 3.1 Add Docker Compose configuration with development PostgreSQL on `5432`.
- [x] 3.2 Add Docker Compose test-profile PostgreSQL on `5433`.
- [x] 3.3 Ensure development and test database environment variables are explicitly separated.

## 4. CI baseline
- [x] 4.1 Add CI workflow to run backend lint and backend unit tests.
- [x] 4.2 Add CI workflow checks for frontend lint, typecheck, and build.
- [x] 4.3 Ensure CI uses project-local scripts/targets rather than ad-hoc commands.

## 5. Testing baseline
- [x] 5.1 Add backend unit test framework setup with mock-based isolation.
- [x] 5.2 Add representative backend unit tests for service-level logic and dependency mocking.
- [x] 5.3 Confirm no backend integration DB tests are required in this change.
- [x] 5.4 Confirm frontend tests are out of scope in this change.

## 6. Validation
- [x] 6.1 Run `openspec validate setup-project-foundation --strict` before implementation.
- [x] 6.2 Run backend lint and unit tests successfully.
- [x] 6.3 Run frontend lint, typecheck, and build successfully.
- [x] 6.4 Run `openspec validate setup-project-foundation --strict` after implementation updates.
