## Summary

Fix several dashboard workflow issues by making the watchlist saved-coins area scrollable, wiring watchlist `Add alert` actions into the alert-creation flow, removing automatic coin preselection from the standard `New alert` flow, and moving Telegram integration management into the dashboard `Settings` workspace with a redirect from the legacy `Integrations` route.

## Problem

The current dashboard flow has several UX inconsistencies:

- the watchlist saved-coins area does not explicitly support scrolling when the list grows
- the watchlist `Add alert` action does not open alert creation
- the standard `New alert` flow automatically selects the first watchlist coin instead of requiring explicit user choice
- Telegram integration management lives in a separate `Integrations` workspace while the user menu already exposes `Settings`
- the sidebar still shows unused navigation entries that do not represent active product workflows

These issues make watchlist and alert authoring feel less predictable and leave the dashboard navigation with duplicate or dead-end entry points.

## Proposed Solution

Introduce a focused frontend-behavior change across the `watchlists`, `alerts`, and `telegram` domains:

- require the watchlist saved-coins panel to remain usable through an internal scroll region
- make watchlist `Add alert` open the create-alert flow with the chosen coin preselected in the coin step
- keep the direct `New alert` entry flow unselected by default so the user must explicitly choose a watchlist coin
- move Telegram integration management into the protected dashboard `Settings` workspace
- redirect the legacy `/integrations` route to `Settings`
- remove unused dashboard tabs and the duplicate sidebar `Settings` entry so settings are reached from the avatar menu

## Scope

Affected domains:

- `watchlists`
- `alerts`
- `telegram`

Primary workflows:

- authenticated user browses a long saved-coins list in `Watchlist`
- authenticated user starts alert creation from a watchlist asset
- authenticated user starts a normal `New alert` flow from the alerts workspace
- authenticated user manages Telegram integration from `Settings`
- authenticated user reaches legacy `Integrations` links and is redirected safely

## Non-Goals

- changing alert rule semantics, alert evaluation, or alert API contracts
- redesigning the alert stepper beyond coin-selection entry behavior
- adding new settings sections beyond the Telegram integration section needed by this change
- introducing new Telegram bot capabilities
- expanding sidebar cleanup beyond removing clearly unused entries covered by this request

## Impact

This change keeps the existing product capabilities but makes their entry points and navigation more coherent. It clarifies the difference between contextual alert creation and generic alert creation, reduces duplicate dashboard navigation, and prepares `Settings` to host future account and integration features without preserving a separate legacy workspace.
