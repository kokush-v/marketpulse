# MarketPulse Technical Task

## 1. Description

MarketPulse is a web application for tracking stock prices, company news, and user-defined alerts in one place.

The product should let a user:

- create personal watchlists
- add stock tickers to those watchlists
- view current price data and historical charts
- read news related to tracked companies
- configure alert rules
- receive Telegram notifications and daily digests

The MVP is focused on a single user role: authenticated regular users. Each user can access only their own watchlists, alerts, Telegram settings, and notification history.

## 2. Technology Stack

### Backend

| Area | Technology |
| --- | --- |
| Language | Python |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL |
| Testing | Pytest |
| Linting / Formatting | Ruff |
| API Docs | OpenAPI / Swagger |

### Frontend

| Area | Technology |
| --- | --- |
| Framework | Next.js 15+ |
| Language | TypeScript |
| Routing | App Router |
| Styling | TailwindCSS + shadcn/ui |
| Server State | TanStack Query |
| Client State | Zustand |
| Forms | React Hook Form |
| Validation | Zod |
| HTTP Client | Axios |
| Charts | Recharts |

### Infrastructure

| Area | Technology |
| --- | --- |
| Cloud | AWS |
| Auth | Supabase Auth through the backend |
| Containers | Docker |
| CI/CD | GitHub Actions |
| Registry | GitHub Container Registry |
| App Hosting | ECS |
| Secrets | AWS Secrets Manager |
| Monitoring | CloudWatch |

### External Integrations

| Integration | Purpose |
| --- | --- |
| Finnhub API | Quotes, historical data, company news |
| Telegram Bot API | Notifications and bot interaction |

## 3. Database Models

### `users`

Stores authenticated application users.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID / string | Internal user identifier |
| supabase_subject | string | External auth identifier |
| email | string | Unique user email |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

### `watchlists`

User-defined collections of tracked stocks.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| user_id | UUID / string | Owner |
| name | string | Required |
| description | string | Optional |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

### `watchlist_symbols`

Tickers assigned to a watchlist.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| watchlist_id | UUID | Related watchlist |
| ticker | string | Stored in uppercase |
| company_name | string | Optional cached metadata |
| exchange | string | Optional |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

### `price_snapshots`

Latest known quote per ticker.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| ticker | string | Stock ticker |
| current_price | decimal | Latest price |
| previous_close | decimal | Optional |
| change | decimal | Optional |
| change_percent | decimal | Optional |
| source | string | Provider name |
| synced_at | datetime | Last sync time |

### `price_history`

Historical OHLCV data for charts.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| ticker | string | Stock ticker |
| date | date | Candle date |
| open | decimal | Optional |
| high | decimal | Optional |
| low | decimal | Optional |
| close | decimal | Required |
| volume | integer | Optional |
| source | string | Provider name |

### `news_articles`

Cached news for tracked companies.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| ticker | string | Related stock |
| title | string | Required |
| summary | text | Optional |
| source | string | Publisher |
| url | string | Unique article URL |
| image_url | string | Optional |
| published_at | datetime | Publication time |
| provider | string | External provider |
| created_at | datetime | Stored at |

### `alert_rules`

User-defined conditions for price or news notifications.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| user_id | UUID / string | Owner |
| ticker | string | Must belong to user's watchlist |
| type | enum | `price_above`, `price_below`, `daily_change_above`, `daily_change_below`, `news_keyword` |
| target_value | string / decimal | Depends on alert type |
| is_active | boolean | Active flag |
| cooldown_minutes | integer | Prevents spam |
| last_triggered_at | datetime | Optional |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

### `telegram_connections`

Stores Telegram linkage and user notification preferences.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| user_id | UUID / string | Owner |
| telegram_chat_id | string | Telegram target |
| is_connected | boolean | Connection status |
| notifications_enabled | boolean | Master toggle |
| daily_digest_enabled | boolean | Digest toggle |
| daily_digest_time | time | Preferred delivery time |
| max_notifications_per_day | integer | Anti-spam limit |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

### `telegram_connection_codes`

Temporary codes used to link a Telegram account.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| user_id | UUID / string | Owner |
| code | string | One-time code |
| expires_at | datetime | Expiration |
| used_at | datetime | Optional |
| created_at | datetime | Creation timestamp |

### `notifications`

Notification log for alerts, digests, and delivery status.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| user_id | UUID / string | Owner |
| alert_rule_id | UUID | Optional source alert |
| type | enum | `price_alert`, `daily_change_alert`, `news_keyword_alert`, `daily_digest`, `system_message` |
| title | string | Short message title |
| message | text | Notification content |
| channel | enum | `telegram`, `in_app` |
| status | enum | `pending`, `sent`, `failed` |
| sent_at | datetime | Optional |
| created_at | datetime | Creation timestamp |

### `job_logs`

Tracks background task execution and failures.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| job_name | string | Job identifier |
| status | enum | `started`, `success`, `failed` |
| details | text / json | Error or summary payload |
| started_at | datetime | Start time |
| finished_at | datetime | Optional end time |

## 4. Backend Features

- Authentication with Supabase Auth and backend JWT validation.
- User-scoped access control so each user works only with their own data.
- CRUD for watchlists.
- Add and remove ticker symbols inside a watchlist.
- Market data API for current quote, historical chart data, and watchlist overview.
- News API for tracked tickers and watchlists.
- Alert rules CRUD with pause/resume support.
- Alert evaluation logic for price thresholds, daily change thresholds, and news keyword alerts.
- Notification history API.
- Telegram settings API and connection code generation.
- Cached provider integration so external API keys stay only on the backend.
- Validation and duplicate prevention for watchlists, symbols, articles, and alerts.
- Structured error handling, logging, health check endpoint, and automated tests.

## 5. Frontend Features

- Authentication flow with login, logout, and protected routes.
- Watchlists page with create, edit, delete, and symbol management.
- Dashboard with tracked tickers, latest prices, daily change, and sync status.
- Ticker details page with historical chart and recent company news.
- News feed with filtering by watchlist and ticker.
- Alerts UI for creating, editing, pausing, resuming, and deleting rules.
- Telegram settings page with connection status and notification preferences.
- Notification history page.
- Clear loading, empty, and error states for all async screens.
- Responsive layout for desktop and mobile.

## 6. Telegram Bot Features

- Start command and onboarding flow for new users.
- Account linking through a one-time connection code.
- Confirmation message after successful account connection.
- Delivery of alert notifications for price and news events.
- Daily digest delivery for enabled users.
- Safe handling of invalid or expired connection codes.
- Ability to disable notifications from the main app while preserving the Telegram link.
- Delivery result logging for sent and failed bot messages.

## 7. Background Jobs, Cron, and Async Features

- Periodic sync of latest quotes for tracked tickers.
- Periodic sync of historical price data for requested chart ranges.
- Periodic sync of company news for tracked tickers.
- Scheduled evaluation of active alert rules.
- Async sending of Telegram notifications after alert creation.
- Daily digest generation and delivery.
- Retry flow for temporary failures from market/news providers or Telegram.
- Cleanup of expired Telegram connection codes.
- Job logging for sync failures, delivery failures, and repeated provider errors.
- Optional stale-data marking when provider sync fails and cached data is returned.

## 8. SDD Requirements and Deliverables

This project must be executed using a Spec-Driven Development workflow, where the specification is treated as the main source of truth and implementation follows the spec rather than replacing it.

### SDD Process Requirements

- Choose one SDD tool before implementation starts and get approval from an AI leader.
- Write and maintain a project specification before generating implementation tasks.
- Create an implementation plan with milestones, vertical slices, dependencies, and test strategy.
- Implement the project slice by slice, updating the specification first whenever requirements change.
- Commit specification updates, plan updates, and code changes together so git history reflects the SDD workflow.
- Run a dedicated AI-assisted code review pass before marking the project as complete.
- Prepare a short retrospective about where the SDD process helped, slowed down, or reduced ambiguity.

### Required SDD Artifacts

- Product specification document.
- Functional requirements and user flows document.
- Implementation plan document.
- Test strategy document.
- AI code review report in markdown format.
- Final retrospective or write-up with lessons learned.

### Suggested Documentation Structure

- `docs/01-project-brief.md`
- `docs/02-functional-spec.md`
- `docs/03-user-flows.md`
- `docs/04-data-model.md`
- `docs/05-api-contracts.md`
- `docs/06-background-jobs.md`
- `docs/07-implementation-plan.md`
- `docs/08-test-strategy.md`
- `docs/09-ai-review-report.md`
- `docs/10-retrospective.md`

### Evaluation Focus for This Project

- Specification clarity: another engineer should be able to understand the project and implement it from the docs.
- Process adherence: implementation should follow the written spec and plan, not ad-hoc prompting only.
- Review depth: AI review should surface real issues in correctness, security, error handling, testability, and performance.
- Reflection quality: the retrospective should explain actual trade-offs and not just describe the tool.

## 9. Estimated Timeline

Estimated total duration for the MVP: up to 1 month for one engineer working in an SDD workflow.

### Feature Estimates

| Area | Feature | Estimate |
| --- | --- | --- |
| SDD | Tool selection, spec setup, documentation structure | 1-2 days |
| Backend | Project setup, architecture, auth foundation, database setup | 2-3 days |
| Backend | Watchlists and ticker management | 2 days |
| Backend | Market data integration and caching | 3-4 days |
| Backend | News integration and storage | 2-3 days |
| Backend | Alert rules and evaluation logic | 3 days |
| Backend | Telegram connection and notification APIs | 2-3 days |
| Backend | Notification history and delivery logging | 1 day |
| Backend | Background jobs, retries, cron scheduling | 2-3 days |
| Frontend | App setup, auth flow, layout foundation | 2-3 days |
| Frontend | Watchlists UI | 2 days |
| Frontend | Dashboard with quotes and charts | 3 days |
| Frontend | News feed and ticker details pages | 2-3 days |
| Frontend | Alerts management UI | 2 days |
| Frontend | Telegram settings and notification history pages | 1-2 days |
| Bot | Telegram bot flow and message templates | 1-2 days |
| Quality | Tests, bugfixing, AI review pass, final stabilization | 3-4 days |
| Delivery | Retrospective, documentation cleanup, demo preparation | 1-2 days |

### High-Level Milestones

- Week 1: SDD setup, specification, implementation plan, backend and frontend foundations.
- Week 2: Watchlists, market data, news, and first working dashboard flow.
- Week 3: Alerts, Telegram integration, background jobs, and notification flow.
- Week 4: Testing, AI review, fixes, documentation, retrospective, and demo preparation.

### Notes

- These estimates assume MVP scope only.
- Timeline may change depending on depth of tests, infrastructure setup, and quality of the selected SDD tool.
- If the project is implemented in parallel by more than one engineer or agent, the delivery time can be reduced.
