# Change: Redesign The Alerts List

## Summary

Redesign the `Alerts` workspace list so saved alerts are denser, easier to scan, and easier to manage. Add a switchable list/card view, backend-driven filters, and a delete confirmation. The alert create/edit flow is not part of this change.

## Problem

The current `Alerts` workspace renders every alert as a tall card that fills only part of the row. A handful of alerts already needs several screens of scrolling, and the active or paused state of each alert is hard to see at a glance. Cards repeat the same information (the subtitle and the trigger rule), show raw ISO dates for recurring windows, and show a meaningless badge for news alerts. There are no filters, and the alert list endpoint always returns every alert. `Delete` removes an alert immediately without confirmation.

## Proposed Solution

- Show alerts as compact rows by default, with an optional card view the user can switch to.
- Remember the user's chosen view between visits in the browser.
- Keep alerts grouped by coin in both views.
- Let the user filter alerts by status (`All`, `Active`, `Paused`), by coin through search, and by scenario type. Filtering is performed by the backend: the alert list endpoint accepts optional filter parameters and returns the matching alerts together with status counts.
- Make pause and resume a direct on/off control and move secondary actions (edit, delete) into a compact actions menu.
- Remove duplicated text, show readable dates, and drop the meaningless badge from news alerts.
- Ask for confirmation before deleting an alert.

## Scope

- Domain: `alerts`.
- Workflow: the authenticated user opens the `Alerts` workspace, scans, filters, and manages existing alerts.
- Backend: optional `status`, `scenario`, and coin search parameters on the alert list endpoint, filtering scoped to the authenticated user's alerts, plus status counts in the response. Backend tests and Orval client regeneration.
- Frontend: the list UI, view switcher, filter controls wired to the new parameters, and delete confirmation.
- The existing pause, resume, and delete endpoints are reused unchanged.

## Assumptions

- Grouping by coin from the current workspace is kept in both views.
- The preferred view is stored per browser (for example in `localStorage`), not on the backend. If browser storage is unavailable, the default list view is used.
- Filters are not persisted between visits.
- The filter parameters are optional, so existing callers of the list endpoint (such as the alert edit flow) keep receiving all alerts when no filters are sent.
- The status counts reflect the coin search and scenario filters but ignore the selected status, so each status option shows how many alerts it would display.
- No pagination is added; the endpoint still returns all matching alerts.

## Non-Goals

- Redesigning the alert create/edit flow (covered by `change-alert-form-to-side-panel`).
- Database schema changes or migrations.
- New alert scenarios, sorting options, bulk actions, or pagination.
- Persisting the view preference or filters on the backend.

## Impact

- Affected spec: `openspec/specs/alerts/spec.md` (replaces the card-only presentation requirement and extends alert listing).
- Affected code: `backend/app/features/alerts/` (routes, service, repository, schemas), backend alert tests, the regenerated Orval client, and the `Alerts` workspace in the frontend (`frontend/features/alerts/`).
- API contract change on `GET /alerts` (additive: optional query parameters and an added `counts` field), requiring Orval regeneration.
- No migrations.
