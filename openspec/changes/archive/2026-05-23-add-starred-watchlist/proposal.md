## Summary
Add the first dedicated `watchlists` capability for MarketPulse as a protected starred-assets workspace. Authenticated users will have a single personal watchlist of saved crypto assets, a search-driven add flow, a selectable asset list, and context cards that update when the selected asset changes.

## Problem
MarketPulse currently mentions watchlists in project scope, but it does not yet define the actual watchlist product behavior. There is no approved specification for how a user saves assets, how a watchlist route behaves, how selected asset context is shown, or how watchlist-specific actions should work. Without a focused `watchlists` change, implementation risks mixing together watchlist management, market-data presentation, and future alert creation behavior.

## Proposed Solution
Introduce a new `watchlists` capability that standardizes:
- a protected `Watchlist` workspace for authenticated users
- a single user-scoped starred-assets list rather than multiple custom-named watchlists
- a search field with dropdown results that lets users add assets to the starred list
- duplicate prevention so the same asset cannot appear twice in the user's watchlist
- a selected asset state that drives summary, chart, and news cards
- automatic selection behavior for the first saved asset when available
- persistence of the selected asset in `LocalStorage` so page refresh does not reset the active context
- per-item overflow actions for removing an asset and exposing a non-functional `Add alert` placeholder entry point

## Scope
In scope:
- Protected watchlist route and user access expectations
- Single personal starred watchlist behavior
- Search and add flow for saving crypto assets into the watchlist
- Duplicate-prevention behavior for saved assets
- Watchlist list-row behavior, selected state, and auto-selection rules
- Watchlist context cards for summary, chart, and related news
- Empty-state behavior for users with no saved assets
- Placeholder `Add alert` action availability in the item action menu
- Backend API, persistence, OpenAPI, and Orval contract expectations needed for the watchlist flow

Out of scope:
- Multiple watchlists per user
- Reordering, grouping, or manually categorizing saved assets
- Full alert-creation workflows or alert persistence from the watchlist UI
- Portfolio tracking, holdings, PnL, or transaction history
- Offline-first watchlist storage in the browser
- LocalStorage persistence for the watchlist contents themselves

## Non-Goals
- Designing the complete alerts product
- Expanding the public dashboard beyond already approved market overview behavior
- Adding social sharing, collaboration, or shared watchlists
- Defining advanced filtering, sorting, or pagination for large watchlists
- Adding custom watchlist notes or tags

## Impact
Affected domains:
- `watchlists`
- `market-data`
- `api-client-generation`

Primary user workflows:
- Authenticated user opens the `Watchlist` tab
- Authenticated user searches for a crypto asset and stars it into the watchlist
- Authenticated user selects a saved asset and views updated summary, chart, and news cards
- Authenticated user removes an asset from the watchlist
- Authenticated user refreshes the page and returns to the previously selected saved asset when it still exists

System impact:
- Adds the first dedicated `watchlists` specification and likely introduces watchlist persistence
- Requires authenticated backend APIs for reading and mutating user watchlist contents
- Requires typed frontend contracts and Orval regeneration for watchlist APIs
- Reuses market-data and news capabilities to populate selected-asset context cards
- Defers alert creation behavior while still reserving a watchlist action entry point for future work
