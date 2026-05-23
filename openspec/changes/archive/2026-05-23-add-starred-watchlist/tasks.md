## 1. OpenSpec validation

- [x] 1.1 Run `openspec validate add-starred-watchlist --strict` before implementation.

## 2. Backend watchlist persistence and APIs

- [x] 2.1 Add database support for a single user-scoped starred watchlist model or equivalent persistence structure for saved crypto assets.
- [x] 2.2 Enforce authenticated ownership for all watchlist reads and mutations using Supabase-derived user context.
- [x] 2.3 Add backend endpoints and typed schemas to read the user's saved assets, add a saved asset, and remove a saved asset.
- [x] 2.4 Prevent duplicate saved assets within the user's watchlist and return a stable user-facing error outcome for duplicate add attempts.
- [x] 2.5 Define the backend response contract needed to supply selected-asset summary, chart, and related-news content for the watchlist workspace.

## 3. Frontend watchlist workspace

- [x] 3.1 Add a protected `Watchlist` tab or route in the authenticated product workspace.
- [x] 3.2 Build the watchlist layout with a saved-assets list, search input with dropdown results, and selected-asset information cards.
- [x] 3.3 Allow users to star an asset from search results to add it to their single watchlist.
- [x] 3.4 Support selecting a saved asset from the watchlist and update all related cards together.
- [x] 3.5 Add per-item overflow actions for `Delete` and a non-functional `Add alert` placeholder action.
- [x] 3.6 Add explicit empty, loading, and error states for the watchlist workspace and for selected-asset context modules.
- [x] 3.7 Persist the selected saved asset in `LocalStorage` and restore it on reload when the asset is still present; otherwise fall back to the first available saved asset.

## 4. Market-data, news, and client contracts

- [x] 4.1 Provide or adapt backend integration paths that supply selected-asset summary, chart, and news data for the watchlist workspace.
- [x] 4.2 Keep the frontend integrated through the primary FastAPI backend rather than direct provider access.
- [x] 4.3 Regenerate Orval clients for any new or updated watchlist-related backend contracts.

## 5. Tests

- [x] 5.1 Add backend tests for authenticated ownership, duplicate prevention, add/remove flows, and selected-asset data responses.

## 6. Final validation

- [x] 6.1 Run `openspec validate add-starred-watchlist --strict` after implementation updates.
- [x] 6.2 Run relevant backend and frontend quality gates during the implementation PR.
