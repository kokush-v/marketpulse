# Change: Move Alert Create/Edit Into A Side Panel

## Summary

Replace the multi-step alert create/edit page with a single side panel that opens over the `Alerts` list. The panel keeps the interactive price chart prominent, drops the stepper and the extra guidance panels, and is used for both creating and editing alerts.

## Problem

Creating an alert takes four steps (coin, scenario, timing, configure) on a separate page, even though the choices fit one short sentence ("Notify me when BTC rises above $70,000, once"). Timing gets a whole step although it is almost always "one-time". Every step repeats the same selection in extra right-hand panels (`Alert preview`, `Compact guidance`, `Current selection`, `Quick preview`). On the final step the price chart starts its Y axis at $0, so the price line is flattened and clicking the chart to pick a trigger level is impractical.

## Proposed Solution

- Open alert creation and editing in a wide side panel (about 520px on desktop) beside the `Alerts` list, so the list stays visible.
- Use one panel layout for create and edit: coin, scenario (`Price above`, `Price below`, `News`), a large interactive chart with the trigger value control, and a single `Repeat` selector.
- Replace the stepper and the extra guidance panels with a single readable summary line.
- Fit the chart's price axis to the visible price range so the trigger can be placed by clicking the chart.
- Show `News` alerts without a chart or trigger value.
- Use the full screen for the panel on narrow viewports.

## Scope

- Domain: `alerts`.
- Workflows: create an alert, edit an alert, and start alert creation from the `Watchlist` workspace.
- Frontend only. The existing alert create, update, list, and chart-data endpoints are reused unchanged.

## Assumptions

- Existing entry points (the `New alert` action, edit actions, and starting from a watchlist asset) keep working and open the panel over the `Alerts` list.
- Closing the panel without saving discards the unsaved input.
- This change builds on the list in `change-alerts-list-redesign` (view switcher, filters, row actions) and SHOULD be implemented after it, because both touch the `Alerts` workspace.

## Non-Goals

- Backend, database, or API contract changes, and Orval regeneration.
- Changing alert scenarios, trigger semantics, baseline capture, or evaluation behavior.
- Changing the list itself (covered by `change-alerts-list-redesign`).
- Adding new alert types, notification channels, or additional chart scopes.

## Impact

- Affected spec: `openspec/specs/alerts/spec.md` (removes the stepper requirement and updates the coin-selection, scenario, and recurring-date requirements).
- Affected code: the alert create/edit flow in the frontend (`frontend/features/alerts/`), and the Watchlist entry point that starts alert creation.
- No migrations and no OpenAPI changes.
