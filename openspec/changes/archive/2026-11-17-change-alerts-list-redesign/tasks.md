# Tasks

## 1. Backend: Filtering
- [x] 1.1 Add optional `status`, `scenario`, and `q` query parameters (typed enums) to `GET /alerts`.
- [x] 1.2 Apply the filters in the repository query alongside the existing user ownership condition, escaping wildcard characters in `q`.
- [x] 1.3 Add `counts` (`all`, `active`, `paused`) to `AlertListResponse`, computed over alerts matching `q` and `scenario` but not `status`.
- [x] 1.4 Keep response models explicit so the OpenAPI schema stays stable.

## 2. Backend: Tests
- [x] 2.1 Test filtering by status, by scenario, and by coin name/symbol (case-insensitive).
- [x] 2.2 Test combined filters and the no-match result.
- [x] 2.3 Test that `counts` ignore the status filter but respect `q` and `scenario`.
- [x] 2.4 Test that filters never return another user's alerts.
- [x] 2.5 Test that invalid `status` or `scenario` values are rejected and that calls without filters still return all alerts.

## 3. API Client
- [x] 3.1 Export the OpenAPI schema and regenerate the Orval client (`docker compose exec -T -e MARKETPULSE_OPENAPI_URL=http://backend:8000/openapi.json frontend npm run generate:api`).

## 4. Frontend: List Structure
- [x] 4.1 Rework the `Alerts` workspace into a header with view switcher, filter bar, and grouped content.
- [x] 4.2 Implement the compact list view with rows grouped by coin (scenario, rule summary, timing, status, status control, actions menu).
- [x] 4.3 Implement the card view with the same content, grouped by coin.
- [x] 4.4 Remove duplicated subtitle/rule text, format recurring dates readably, and drop the placeholder badge for news alerts.

## 5. Frontend: View Preference
- [x] 5.1 Add the list/card switcher, defaulting to the list view.
- [x] 5.2 Persist the chosen view in browser storage with a safe fallback when storage is unavailable.

## 6. Frontend: Filters
- [x] 6.1 Add the status filter (`All`, `Active`, `Paused`) showing the backend `counts`.
- [x] 6.2 Add coin search (debounced) and the scenario type filter, sending all filters as request parameters.
- [x] 6.3 Add a no-results state with a clear-filters action, and keep the list visible while a filtered request loads.

## 7. Frontend: Lifecycle Actions
- [x] 7.1 Add a pause/resume on/off control per alert and show a readable error when it fails.
- [x] 7.2 Move edit and delete into an actions menu in both views.
- [x] 7.3 Add a delete confirmation dialog with cancel, confirm, and failure handling.
- [x] 7.4 Refresh the filtered list and counts after pause, resume, or delete.

## 8. Frontend: States
- [x] 8.1 Keep loading, error with retry, and first-alert empty states working in both views.

## 9. Validation
- [x] 9.1 Run `docker compose exec -T backend uv run ruff check .` and `docker compose exec -T backend uv run ruff format --check .`.
- [x] 9.2 Run `docker compose exec -T backend uv run pytest tests/unit/features/alerts`.
- [x] 9.3 Run `docker compose exec -T frontend npm run lint`, `npm run typecheck`, and `npm run build`.
- [x] 9.4 Manually verify both views, view persistence, filters and counts, pause/resume, and delete confirmation in the browser, including narrow widths.
- [x] 9.5 Run `openspec validate change-alerts-list-redesign --strict`.
