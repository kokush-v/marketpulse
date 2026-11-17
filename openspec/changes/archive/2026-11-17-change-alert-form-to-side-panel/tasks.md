# Tasks

## 1. Frontend: Panel Shell
- [x] 1.1 Add a side panel for alert authoring that opens next to the `Alerts` list on wide viewports and uses the full screen on narrow viewports.
- [x] 1.2 Keep existing entry points working: `New alert`, edit actions, and starting from a watchlist asset (coin preselected).
- [x] 1.3 Close the panel on cancel or after a successful save and refresh the alert list.

## 2. Frontend: Form Content
- [x] 2.1 Build the coin field from the user's watchlist, with the add-missing-coin action kept inside the panel.
- [x] 2.2 Build the scenario chips (`Price above`, `Price below`, `News`).
- [x] 2.3 Build the trigger value control with the `% / $` toggle and the chart scope switch (`1D`, `1W`, `1M`).
- [x] 2.4 Build the single `Repeat` control (`Once` default, daily within a date range) with a calendar date picker and range validation.
- [x] 2.5 Hide the chart and trigger value for `News` and show the any-new-article description.
- [x] 2.6 Replace the stepper and the preview/guidance panels with a single readable summary line.

## 3. Frontend: Chart
- [x] 3.1 Fit the chart's vertical axis to the displayed price range with padding.
- [x] 3.2 Keep click-to-set trigger and the on-chart trigger line working with the new axis.

## 4. Frontend: Edit And States
- [x] 4.1 Populate the panel from an existing alert when editing, including its trigger line on the chart.
- [x] 4.2 Show loading, error with retry, not-found, and save-failure states without losing entered values.

## 5. Cleanup
- [x] 5.1 Remove the old multi-step page components and routes that are no longer used.

## 6. Validation
- [x] 6.1 Run `docker compose exec -T frontend npm run lint`.
- [x] 6.2 Run `docker compose exec -T frontend npm run typecheck`.
- [x] 6.3 Run `docker compose exec -T frontend npm run build`.
- [x] 6.4 Manually verify create (all three scenarios), edit (price and news), daily range, add-missing-coin, watchlist entry, and narrow-width behavior in the browser.
- [x] 6.5 Run `openspec validate change-alert-form-to-side-panel --strict`.
