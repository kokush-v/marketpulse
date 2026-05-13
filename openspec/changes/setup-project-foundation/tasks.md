## 1. Backend scaffold
- [ ] 1.1 Create backend project baseline with FastAPI application entrypoint and health endpoint.
- [ ] 1.2 Configure async SQLAlchemy session setup using `asyncpg`.
- [ ] 1.3 Initialize Alembic baseline wiring for async SQLAlchemy models.
- [ ] 1.4 Add backend lint/format configuration and runnable project scripts/targets.

## 2. Frontend scaffold
- [ ] 2.1 Create Next.js App Router baseline with TypeScript.
- [ ] 2.2 Configure TailwindCSS and shadcn/ui baseline setup.
- [ ] 2.3 Configure TanStack Query provider baseline for app routing tree.
- [ ] 2.4 Add Orval configuration for generating frontend API clients from backend OpenAPI.
- [ ] 2.5 Add frontend runnable scripts for lint, typecheck, and build.

## 3. Infrastructure baseline
- [ ] 3.1 Add Docker Compose configuration with development PostgreSQL on `5432`.
- [ ] 3.2 Add Docker Compose test-profile PostgreSQL on `5433`.
- [ ] 3.3 Ensure development and test database environment variables are explicitly separated.

## 4. CI baseline
- [ ] 4.1 Add CI workflow to run backend lint and backend unit tests.
- [ ] 4.2 Add CI workflow checks for frontend lint, typecheck, and build.
- [ ] 4.3 Ensure CI uses project-local scripts/targets rather than ad-hoc commands.

## 5. Testing baseline
- [ ] 5.1 Add backend unit test framework setup with mock-based isolation.
- [ ] 5.2 Add representative backend unit tests for service-level logic and dependency mocking.
- [ ] 5.3 Confirm no backend integration DB tests are required in this change.
- [ ] 5.4 Confirm frontend tests are out of scope in this change.

## 6. Validation
- [ ] 6.1 Run `openspec validate setup-project-foundation --strict` before implementation.
- [ ] 6.2 Run backend lint and unit tests successfully.
- [ ] 6.3 Run frontend lint, typecheck, and build successfully.
- [ ] 6.4 Run `openspec validate setup-project-foundation --strict` after implementation updates.
