## ADDED Requirements

### Requirement: Provide Project Foundation for Backend and Frontend
The system SHALL provide an initialized project foundation that includes backend and frontend starter architectures aligned with project conventions.

#### Scenario: Backend foundation is initialized
- **Given** a developer clones the repository
- **When** the backend foundation setup is completed
- **Then** the repository contains a runnable FastAPI baseline with async SQLAlchemy and Alembic configuration

#### Scenario: Frontend foundation is initialized
- **Given** a developer clones the repository
- **When** the frontend foundation setup is completed
- **Then** the repository contains a runnable Next.js App Router baseline with TailwindCSS, shadcn/ui, and TanStack Query configuration

### Requirement: Provide Orval Generation Baseline
The system SHALL include Orval configuration to enable frontend API client generation from backend OpenAPI schema.

#### Scenario: API client generation config is present
- **Given** backend OpenAPI schema is available
- **When** a developer runs configured API client generation command
- **Then** Orval is configured to generate frontend API client artifacts without manual type duplication

### Requirement: Separate Development and Test Databases
The system SHALL provide separate PostgreSQL runtime services for development and test execution with distinct ports.

#### Scenario: Development database service
- **Given** local development runtime is started
- **When** Docker Compose starts database services
- **Then** development PostgreSQL is reachable on port `5432`

#### Scenario: Test database service
- **Given** local test runtime is started with test profile
- **When** Docker Compose starts test database services
- **Then** test PostgreSQL is reachable on port `5433`

### Requirement: Enforce Foundation Quality Gates in CI
The system SHALL run baseline backend and frontend quality checks in CI.

#### Scenario: Backend quality checks
- **Given** a change is pushed
- **When** CI executes backend checks
- **Then** backend lint and backend unit test checks are executed

#### Scenario: Frontend quality checks
- **Given** a change is pushed
- **When** CI executes frontend checks
- **Then** frontend lint, typecheck, and build checks are executed

### Requirement: Limit Foundation Tests to Backend Unit Tests
The system SHALL provide backend unit testing with mock-based isolation as the only required test category in this change.

#### Scenario: Backend unit test execution
- **Given** backend foundation test configuration exists
- **When** backend tests are executed for this change
- **Then** required tests are unit tests that use mocks instead of live infrastructure dependencies
