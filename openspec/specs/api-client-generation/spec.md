# api-client-generation Specification

## Purpose
TBD - created by archiving change setup-project-foundation. Update Purpose after archive.
## Requirements
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

### Requirement: Enforce Local Pre-Commit Lint Checks
The system SHALL provide a local pre-commit workflow that runs repository-defined lint checks for both backend and frontend code before a Git commit is created.

#### Scenario: Developer creates a commit with passing lint checks
- **Given** a developer has installed the repository's local commit hooks
- **When** the developer creates a Git commit
- **Then** the local workflow runs the backend lint check for the backend codebase
- **And** the local workflow runs the frontend lint check for the frontend codebase
- **And** the commit is allowed to proceed if both lint checks pass

#### Scenario: Developer creates a commit with a failing lint check
- **Given** a developer has installed the repository's local commit hooks
- **And** either the backend lint check or the frontend lint check fails
- **When** the developer creates a Git commit
- **Then** the local workflow blocks commit creation

### Requirement: Run Whole-Codebase Lint Checks In Local Hooks
The system SHALL run whole-codebase lint checks in the local pre-commit workflow rather than limiting validation to staged files only.

#### Scenario: Developer commits with changes in only part of the repository
- **Given** a developer has staged changes in only a subset of files
- **When** the local pre-commit workflow starts
- **Then** the backend lint check evaluates the configured backend codebase
- **And** the frontend lint check evaluates the configured frontend codebase
- **And** the workflow does not limit either lint check to staged files only

### Requirement: Use Local-Only Hook Enforcement
The system SHALL scope this lint enforcement to local commit hooks and SHALL NOT require new CI behavior as part of this change.

#### Scenario: Local hooks are introduced without changing CI scope
- **Given** the repository already has CI quality checks
- **When** this change is implemented
- **Then** the new lint enforcement is introduced through local commit hooks
- **And** CI requirements remain unchanged by this change

### Requirement: Provide Frontend Jest Test Foundation
The system SHALL provide a Jest-based frontend automated test foundation for the Next.js application.

#### Scenario: Frontend Jest foundation is available
- **Given** the frontend codebase includes reusable modules, hooks, and interactive components
- **When** a developer prepares frontend automated tests
- **Then** the project provides an approved Jest-based test foundation for frontend unit and component testing

### Requirement: Provide A Standard Frontend Test Command
The system SHALL provide a standard frontend package command for local automated test execution.

#### Scenario: Developer runs frontend automated tests locally
- **Given** the frontend dependencies are installed
- **When** a developer runs the standard frontend test command
- **Then** the frontend automated tests execute through the approved Jest runner

### Requirement: Scope Initial Frontend Automated Tests To Logic-Heavy Surfaces
The system SHALL require the initial frontend automated testing scope to focus on reusable `lib` modules, custom `hooks`, and critical interactive components.

#### Scenario: Developer adds tests for approved frontend surfaces
- **Given** a frontend change affects reusable application logic, custom hook behavior, or a critical interactive component
- **When** automated frontend tests are added or updated for that change
- **Then** the tests target those approved surfaces as the required initial scope

#### Scenario: Developer evaluates simple UI primitives
- **Given** a frontend component is a simple presentational primitive without meaningful project-specific behavior
- **When** a developer decides whether it requires automated coverage under this change
- **Then** the project does not require that primitive to be covered by default

### Requirement: Run Frontend Automated Tests In CI
The system SHALL execute frontend automated tests in CI as part of the frontend quality gates.

#### Scenario: CI runs frontend quality checks for a change
- **Given** a change is pushed to the repository
- **When** CI executes frontend quality checks
- **Then** CI runs the standard frontend automated test command
- **And** CI keeps frontend lint and typecheck execution as part of the frontend quality bar

