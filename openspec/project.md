# MarketPulse Project Guide

## Project Context

MarketPulse is a web application for authenticated users who want to track cryptocurrency prices, market news, alert rules, and Telegram notifications in one place.

The MVP is focused on one user role: authenticated regular users.

Every user can access only their own:

- watchlists
- symbols
- alert rules
- Telegram connection
- notification settings
- notification history

## Product Scope

MarketPulse MVP lets authenticated users:

- create and manage personal crypto watchlists
- add, remove, and inspect cryptocurrency assets
- view latest price data, daily movement, sync status, and historical charts
- view market news related to tracked assets
- create, pause, resume, and delete alert rules
- receive Telegram notifications for alert triggers and optional daily digests

Provider API keys and Telegram bot tokens must stay on the backend only.

## Technology Stack

### Backend

- FastAPI with async route handlers where I/O is involved
- SQLAlchemy async ORM
- asyncpg as the PostgreSQL async driver
- Alembic for migrations
- Pydantic
- Pytest
- pytest-asyncio
- Ruff
- uv
- OpenAPI / Swagger
- Supabase Auth
- Supabase async Python client when server-side Supabase API access is needed
- PyJWT or python-jose for local JWT verification
- aiogram for async Telegram Bot API integration

### Frontend

- Next.js 15+ with App Router
- TypeScript
- TailwindCSS
- shadcn/ui
- TanStack Query
- Zustand when needed
- React Hook Form
- Zod
- Axios
- Recharts
- Orval for generating type-safe API clients from the backend OpenAPI schema
- Generated React Query hooks should be preferred over manually written API hooks when practical

### Infrastructure

- Supabase Auth, accessed through the backend only for protected API authorization
- Docker
- GitHub Actions
- GitHub Container Registry
- AWS ECS
- AWS Secrets Manager
- AWS CloudWatch

### External Integrations

- Crypto market data providers for prices, historical data, metadata, and market news
- Telegram Bot API for notification delivery and account linking

## Domain Model

Core entities:

- `users`: local representation of authenticated Supabase Auth users
- `watchlists`: user-owned groups of tracked crypto assets
- `watchlist_symbols`: asset symbols assigned to watchlists
- `price_snapshots`: latest known quote per tracked asset
- `price_history`: historical OHLCV data for charts
- `news_articles`: cached crypto market news from providers
- `alert_rules`: user-defined price, daily-change, and news-keyword conditions
- `telegram_connections`: Telegram linkage and notification preferences
- `telegram_connection_codes`: temporary one-time codes for linking Telegram
- `notifications`: alert, digest, and system notification history
- `job_logs`: background task execution records

## Architecture Principles

- Treat the backend as the trusted boundary for authentication, authorization, provider calls, caching, and notification delivery.
- Scope all user-owned resources by the authenticated user.
- Never trust client-supplied ownership identifiers when the backend can derive ownership from the JWT.
- Store tracked asset symbols in uppercase.
- Keep provider credentials and Telegram bot tokens out of frontend code.
- Cache external provider data where practical to reduce API usage and improve UX.
- Prefer explicit service boundaries for market data, news, alerts, Telegram, and background jobs.
- Keep API responses stable and documented through OpenAPI.
- Favor small, testable units for alert evaluation and provider adapters.
- Keep the OpenAPI schema stable enough to support Orval-based frontend client generation.

## Backend Feature Structure

Use feature-based FastAPI structure:

```text
app/
  features/
    <feature_name>/
      routes.py
      service.py
      schemas.py
      models.py
      dependencies.py
      repository.py
  tests/
```

Feature file responsibilities:

- `routes.py` defines HTTP endpoints only.
- `service.py` contains business logic.
- `repository.py` contains database access when queries become non-trivial.
- `schemas.py` contains Pydantic request and response schemas.
- `models.py` contains SQLAlchemy models.
- `dependencies.py` contains feature-specific FastAPI dependencies.

Tests

- `tests/` should mirror the feature structure for test organization.

## Backend Conventions

- Use FastAPI dependency injection for auth, database sessions, and shared services.
- Validate Supabase Auth JWTs on protected endpoints.
- Derive the current user from the validated JWT and local `users` record.
- Enforce row ownership in queries, not only at the route layer.
- Use SQLAlchemy models and Alembic migrations for schema changes.
- Use Pydantic schemas for request and response validation.
- Keep response models explicit so the generated OpenAPI schema remains useful for Orval.
- Normalize tracked asset symbols before persistence and comparison.
- Prevent duplicate watchlist names per user where appropriate.
- Prevent duplicate asset symbols inside the same watchlist.
- Prevent duplicate news articles by URL.
- Represent alert rule types with explicit enums:
   - `price_above`
   - `price_below`
   - `daily_change_above`
   - `daily_change_below`
   - `news_keyword`
- Use alert cooldowns and daily notification limits to avoid notification spam.
- Log background job outcomes in `job_logs`.

## Authentication Conventions

- Supabase Auth is the authentication provider.
- The backend is responsible for validating access tokens on protected endpoints.
- The frontend may obtain and store Supabase sessions, but protected business data must come from the backend API.
- Backend routes must not trust user IDs sent in request bodies or query parameters when ownership can be derived from the authenticated user.
- Local `users` records should map application data to Supabase Auth users.
- Auth-related code should be isolated in a dedicated `auth` feature or shared security module.

## Frontend Conventions

- Use protected routes for authenticated product screens.
- Prefer practical application UI over marketing-style pages.
- Use shadcn/ui components consistently.
- Use TanStack Query for API fetching, cache state, loading states, and error states.
- Use Orval-generated API clients and React Query hooks where practical.
- Do not duplicate API request and response types manually if they can be generated from OpenAPI.
- Use React Hook Form with Zod schemas for forms.
- Show clear loading, empty, and error states for every async screen.
- Keep crypto tracking and alert workflows efficient.
- Watchlists, symbols, alerts, Telegram settings, and notification history should be easy to scan and manage.

## API Client Generation Rules

- Backend OpenAPI output is the source of truth for generated frontend API clients.
- Orval should generate TypeScript clients from the FastAPI OpenAPI schema.
- Prefer generated React Query hooks for standard CRUD and read flows.
- Use custom frontend API code only when generated clients are not practical.
- Keep backend response schemas stable and explicit to avoid breaking generated frontend code.
- When an endpoint contract changes, update backend schemas, regenerate the frontend client, and adjust affected UI code in the same change.

## OpenSpec Conventions

- Current approved behavior belongs in `openspec/specs/<domain>/spec.md`.
- Proposed work belongs in `openspec/changes/<change-id>/`.
- Use focused capability domains:
   - `auth`
   - `watchlists`
   - `market-data`
   - `news`
   - `alerts`
   - `telegram`
   - `notifications`
   - `background-jobs`
   - `api-client-generation`
- Use verb-led change IDs:
   - `add-watchlist-management`
   - `add-telegram-linking`
   - `change-alert-rule-cooldowns`
   - `fix-watchlist-symbol-duplicates`
   - `add-orval-client-generation`
- Write requirements with RFC-style language:
   - `SHALL` for required behavior
   - `SHOULD` for recommended behavior
   - `MAY` for optional behavior
- Write scenarios in Given / When / Then format.
- Include non-goals in proposals when scope could expand.
- Keep implementation tasks small enough to complete and verify independently.
- If implementation discoveries conflict with the approved spec, stop and ask for clarification before changing scope.

## OpenSpec Workflow Rules

- Do not implement code without an approved OpenSpec change.
- Do not invent requirements.
- Do not add out-of-scope functionality.
- Validate every change before implementation:

```bash
openspec validate <change-id> --strict
```

- Follow `tasks.md` during implementation.
- Update `tasks.md` only after the related code and tests are actually complete.
- Run relevant tests after implementation.
- Run OpenSpec validation again after implementation.

## Agent Context Rules

- Do not read the entire repository unless explicitly required.
- Start from OpenSpec files for the selected change.
- Inspect only files related to the current tasks.
- Do not infer hidden requirements from unrelated code.
- Do not change approved scope without asking.
- Summarize assumptions before implementation.
- Prefer minimal, targeted edits over broad refactoring.
- Do not introduce unrelated abstractions.

## Quality Bar

- New backend behavior should include focused Pytest coverage.
- New frontend flows should include validation, loading, empty, and error states.
- Security-sensitive changes require explicit ownership and authorization checks.
- External API integration code should handle provider failures, rate limits, and malformed responses.
- Background jobs should be observable through logs and `job_logs`.
- Notification behavior should be idempotent where possible to avoid duplicate sends.
- API contract changes should keep OpenAPI and Orval-generated frontend code in sync.
