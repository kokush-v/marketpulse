# Project Context

MarketPulse is a web application for authenticated users who want to track stock prices, company news, alert rules, and Telegram notifications in one place.

The MVP is focused on a single user role: authenticated regular users. Every user can access only their own watchlists, symbols, alert rules, Telegram connection, notification settings, and notification history.

## Product Goals

- Let users create and manage personal stock watchlists.
- Let users add, remove, and inspect stock tickers in watchlists.
- Show latest quote data, daily movement, sync status, and historical charts.
- Show company news related to tracked tickers.
- Let users create, pause, resume, and delete alert rules.
- Send Telegram notifications for alert triggers and optional daily digests.
- Keep external provider API keys on the backend only.

## Technology Stack

### Backend

- Python with FastAPI.
- SQLAlchemy for ORM models.
- Alembic for database migrations.
- PostgreSQL as the primary database.
- Pytest for tests.
- Ruff for linting and formatting.
- OpenAPI / Swagger for API documentation.

### Frontend

- Next.js 15+ with the App Router.
- TypeScript.
- TailwindCSS and shadcn/ui.
- TanStack Query for server state.
- Zustand for client state when needed.
- React Hook Form and Zod for forms and validation.
- Axios for HTTP calls.
- Recharts for charts.

### Infrastructure

- Supabase Auth for authentication, accessed through the backend only.
- Docker containers.
- GitHub Actions for CI/CD.
- GitHub Container Registry for images.
- AWS ECS for app hosting.
- AWS Secrets Manager for secrets.
- AWS CloudWatch for logs and monitoring.

### External Integrations

- Finnhub API for quotes, historical data, and company news.
- Telegram Bot API for notification delivery and account-linking interaction.

## Domain Model

Core entities:

- `users`: local representation of authenticated Supabase Auth users.
- `watchlists`: user-owned groups of tracked stocks.
- `watchlist_symbols`: tickers assigned to watchlists.
- `price_snapshots`: latest known quote per ticker.
- `price_history`: historical OHLCV data for charts.
- `news_articles`: cached company news from providers.
- `alert_rules`: user-defined price, daily-change, and news-keyword conditions.
- `telegram_connections`: Telegram linkage and notification preferences.
- `telegram_connection_codes`: temporary one-time codes for linking Telegram.
- `notifications`: alert, digest, and system notification history.
- `job_logs`: background task execution records.

## Architecture Principles

- Treat the backend as the trusted boundary for authentication, authorization, provider calls, caching, and notification delivery.
- Scope all user-owned resources by the authenticated user.
- Never trust client-supplied ownership identifiers when the backend can derive ownership from the JWT.
- Store stock tickers in uppercase.
- Keep provider credentials and Telegram bot tokens out of frontend code.
- Cache external provider data where practical to reduce API usage and improve UX.
- Prefer explicit service boundaries for market data, news, alerts, Telegram, and background jobs.
- Keep API responses stable and documented through OpenAPI.
- Favor small, testable units for alert evaluation and provider adapters.

## Backend Conventions

- Use FastAPI dependency injection for auth, database sessions, and shared services.
- Validate Supabase Auth JWTs on protected endpoints.
- Enforce row ownership in queries, not only at the route layer.
- Use SQLAlchemy models and Alembic migrations for schema changes.
- Use Pydantic schemas for request and response validation.
- Normalize tickers before persistence and comparison.
- Prevent duplicate watchlist names per user where appropriate.
- Prevent duplicate tickers inside the same watchlist.
- Prevent duplicate news articles by URL.
- Represent alert rule types with explicit enums:
  - `price_above`
  - `price_below`
  - `daily_change_above`
  - `daily_change_below`
  - `news_keyword`
- Use alert cooldowns and daily notification limits to avoid notification spam.
- Log background job outcomes in `job_logs`.

## Frontend Conventions

- Use protected routes for authenticated product screens.
- Prefer practical application UI over marketing-style pages.
- Use shadcn/ui components consistently.
- Use TanStack Query for API fetching, cache state, loading states, and error states.
- Use React Hook Form with Zod schemas for forms.
- Show clear loading, empty, and error states for every async screen.
- Keep stock and alert workflows efficient: watchlists, symbols, alerts, Telegram settings, and notification history should be easy to scan and manage.

## OpenSpec Conventions

- Current behavior belongs in `openspec/specs/<domain>/spec.md`.
- Proposed work belongs in `openspec/changes/<change-id>/`.
- Use focused capability domains such as:
  - `auth`
  - `watchlists`
  - `market-data`
  - `news`
  - `alerts`
  - `telegram`
  - `notifications`
  - `background-jobs`
- Write requirements with RFC-style language:
  - `SHALL` for required behavior.
  - `SHOULD` for recommended behavior.
  - `MAY` for optional behavior.
- Write scenarios in Given / When / Then format.
- Include non-goals in proposals when scope could expand.
- Keep implementation tasks small enough to complete and verify independently.
- Update specs when implementation discoveries change expected behavior.

## Quality Bar

- New backend behavior should include focused Pytest coverage.
- New frontend flows should include validation, loading, empty, and error states.
- Security-sensitive changes require explicit ownership and authorization checks.
- External API integration code should handle provider failures, rate limits, and malformed responses.
- Background jobs should be observable through logs and `job_logs`.
- Notification behavior should be idempotent where possible to avoid duplicate sends.

## MVP Non-Goals

- Multiple user roles or admin dashboards.
- Social sharing or collaborative watchlists.
- Brokerage trading or order placement.
- Paid subscription management.
- Multi-provider market data abstraction beyond the first Finnhub integration, unless needed for testing or clean boundaries.
