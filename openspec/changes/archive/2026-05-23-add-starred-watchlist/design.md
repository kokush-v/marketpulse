## Overview
This change defines the first dedicated watchlist product workflow for MarketPulse. The watchlist is intentionally narrow in its first version: each authenticated user gets one personal starred-assets list, uses search to add assets into it, and views selected-asset context through summary, chart, and news cards. The change avoids introducing multiple named watchlists or full alert creation so the first implementation stays focused.

## Architectural Decisions

### 1. Single watchlist model
- Each authenticated user shall have one personal watchlist concept representing saved or starred crypto assets.
- The first version shall not support multiple user-created watchlists, watchlist naming, or watchlist organization features.
- The product language should consistently describe the list as the user's saved, starred, or watchlist assets rather than implying a broader portfolio model.

### 2. Protected workspace access
- The watchlist workspace is a functional product surface and shall require authentication.
- Backend ownership for watchlist resources shall be derived from the authenticated user context rather than any client-supplied user identifier.
- Requests for watchlist data or mutations without valid authentication shall be rejected according to the existing auth specification.

### 3. Persistence model
- The system shall persist watchlist contents on the backend as user-owned data rather than relying on browser-only storage.
- The system shall prevent duplicate saved assets inside a user's watchlist.
- Asset identifiers should be normalized according to existing project conventions for uppercase tracked symbols when symbol persistence or comparison is involved.
- This change likely requires database schema and migration work for watchlist persistence unless an equivalent approved structure already exists.

### 4. Selected asset state
- The UI shall maintain a single selected asset within the user's saved-assets list.
- When the watchlist contains one or more saved assets and there is no valid restored selection, the UI shall auto-select the first available saved asset.
- The frontend shall persist only the selected asset reference in `LocalStorage` so reloads preserve context.
- If `LocalStorage` points to an asset that is no longer in the watchlist, the system shall gracefully fall back to the first available saved asset.
- `LocalStorage` is a convenience for UI continuity only and shall not be treated as the source of truth for watchlist membership.

### 5. Search and add workflow
- The watchlist workspace shall expose a search field with dropdown results that allows a user to star an asset into the watchlist.
- The star action represents adding the asset into the single personal watchlist.
- Duplicate add attempts should not create a second entry and should return a stable, user-visible outcome.
- This change does not require advanced search features such as fuzzy ranking customization, recent searches, or bulk add flows.

### 6. Selected-asset context cards
- Selecting an asset from the watchlist shall update all dependent cards together.
- The first version shall include:
  - a summary card for key market information such as price, 24-hour change, market cap, and volume
  - a chart card
  - a related news card
- The watchlist capability may depend on existing or extended `market-data` and `news` integrations, but the frontend should receive those through backend-owned contracts.

### 7. Overflow actions and alert placeholder
- Each saved-asset row shall expose an overflow action menu.
- The first version shall provide a `Delete` action that removes the asset from the watchlist.
- The first version may show an `Add alert` action as a placeholder entry point, but it shall not create, persist, or modify alerts yet.
- Future alert integration should be specified in a separate `alerts` or cross-domain change instead of expanding this watchlist scope.

## Security and Ownership
- Watchlist membership is user-owned data and must not be accessible across users.
- The backend must derive ownership from authenticated context and enforce it in queries and mutations.
- The frontend must not trust browser state alone for watchlist membership.
- As with other protected workflows, provider credentials and backend integration details must remain server-side.

## API and Client Contract Notes
- The backend should expose explicit authenticated watchlist contracts for list retrieval and membership mutations.
- If selected-asset context is served through the same route or adjacent routes, those response schemas should remain explicit and stable for Orval generation.
- The frontend should continue to consume watchlist data only through the FastAPI backend API surface.
- If market or news payloads are reused for watchlist cards, the backend may compose or proxy them as needed, but the observable frontend behavior should remain stable.

## Risks and Rollback Considerations
- Risk: a single-watchlist model may need later expansion into multiple named watchlists.
- Mitigation: keep naming and persistence structures straightforward so a later change can extend them deliberately.
- Risk: selected-asset restoration can point at stale browser state after deletions.
- Mitigation: explicitly fall back to the first available asset or an empty state.
- Risk: watchlist and alert scopes could become coupled too early.
- Mitigation: keep `Add alert` as a non-functional placeholder in this change and defer alert behavior to a future approved change.
- Rollback: the watchlist route can be disabled independently while leaving broader market-data capabilities intact if the dedicated watchlist implementation needs to be reverted.
