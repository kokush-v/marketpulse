## 1. Backend

- [x] 1.1 Update the protected FastAPI alerts feature so the create and update contract models one alert scenario at a time instead of multi-condition authoring.
- [x] 1.2 Keep a stable alert domain model that supports user ownership, active/paused status, selected coin context, and one stored scenario per alert.
- [x] 1.3 Implement backend validation for the three supported scenarios only: `price_above`, `price_below`, and `coin_news`, with `% / $` trigger modes for price scenarios.
- [x] 1.4 Ensure backend ownership enforcement derives the current user from authentication and never trusts client-supplied ownership identifiers.
- [x] 1.5 Enforce the watchlist-scoped coin-selection rule so alert creation and editing operate on the authenticated user's watchlist assets or through the explicit add-to-watchlist path.
- [x] 1.6 Provide alert response fields that let the frontend render coin name, readable rule summaries, current status, scenario details for edit flows, and available actions without reconstructing business rules client-side.
- [x] 1.7 Extend the alerts contract to support both `one-time` and `daily recurring` time-behavior modes for all alert types.
- [x] 1.8 Validate recurring alert date windows and expose enough state for future once-per-day trigger enforcement.

## 2. Database

- [x] 2.1 Add or update database schema and Alembic migrations for alert persistence, including user ownership, one stored scenario per alert, status fields, and any creation-time baseline data needed for percentage rules.
- [x] 2.2 Add database-level constraints or model validation that prevent invalid alert states and keep stored symbols normalized to uppercase where symbols are persisted.
- [x] 2.3 Persist alert time-behavior mode plus recurring start/end dates and any state needed for future one-trigger-per-day evaluation.

## 3. API Client Generation

- [x] 3.1 Update backend OpenAPI output for the revised alerts-management contract.
- [x] 3.2 Regenerate Orval frontend API client artifacts for the revised alerts endpoints.

## 4. Frontend

- [x] 4.1 Keep a protected `Alerts` workspace that lists the authenticated user's alerts as cards.
- [x] 4.2 Rework create and edit flows so they start with watchlist-scoped coin selection and then present only the `Price above`, `Price below`, and `News` scenarios.
- [x] 4.3 Add an inline add-to-watchlist action in alert creation and editing so a missing coin can be saved and selected without leaving the flow.
- [x] 4.4 Build a stepper-based create/edit experience and use the requested `@reui/c-stepper-9` shadcn integration when implementing the stepper.
- [x] 4.5 Build a chart-first authoring experience for `Price above` and `Price below` flows.
- [x] 4.6 Add chart scope switching for `1D`, `1W`, and `1M`.
- [x] 4.7 Add a single trigger-value control for price alerts with a right-aligned `% / $` toggle.
- [x] 4.8 Display the configured trigger value directly on the chart while the user edits price alerts.
- [x] 4.9 Ensure `News` uses a simpler scenario flow without unnecessary chart interaction.
- [x] 4.10 Preserve pause, resume, and delete actions on alert cards with clear success and failure handling.
- [x] 4.11 Add lightweight step and scenario animations where they help the user maintain context.
- [x] 4.12 Replace the large builder-notes side panel with smaller inline or contextual guidance that does not dominate the layout.
- [x] 4.13 Add explicit loading, empty, validation-error, and request-error states for alerts listing and alert authoring flows.
- [x] 4.14 Add a time-behavior step or section that lets the user choose `one-time` or `daily recurring` for all alert types.
- [x] 4.15 Add a shadcn/ui calendar-based start-date and end-date picker for recurring alerts.
- [x] 4.16 Surface recurring behavior clearly in alert cards and edit flows.

## 5. Tests

- [x] 5.1 Add backend tests for authenticated access, unauthenticated rejection, and row ownership on all alerts-management operations.
- [x] 5.2 Add backend tests for absolute-value price rules, percentage-based rules through the `% / $` trigger model, and news-subscription validation.
- [x] 5.3 Add backend tests for watchlist-scoped alert creation behavior and the add-to-watchlist path when it changes backend contracts.
- [x] 5.4 Add backend tests for one-time alerts, recurring date-range validation, and recurring once-per-day eligibility modeling.
- [x] 5.5 Run `openspec validate add-alert-management --strict`.
