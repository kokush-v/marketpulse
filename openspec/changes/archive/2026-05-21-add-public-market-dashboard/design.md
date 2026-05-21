## Overview
This change introduces a public crypto market dashboard foundation that combines a reusable dashboard shell with a dedicated Ruby on Rails microservice for CoinGecko-backed crypto market data. The first delivery is intentionally lightweight: it prioritizes a polished public crypto market overview page and leaves persistence, caching, and expanded personalization for later changes.

## Architectural Decisions

### 1. Public dashboard access model
- The dashboard foundation is public and does not require authentication to load.
- The first tab is a general crypto market overview rather than a user-scoped portfolio view.
- Authenticated users MAY see additional watchlist-related context when such data exists, but this must not change the page into a protected route.

### 2. Dashboard shell structure
- The frontend shall establish a reusable shell with:
  - left or top navigation for current and future dashboard tabs
  - a consistent header region for page identity and actions
  - a main content region that hosts tab-specific modules
- The first tab shall be the default landing tab of this shell.
- Future tabs should be added inside this shell rather than redesigning the dashboard layout.

### 3. Dedicated Ruby market-data microservice boundary
- A new or repurposed root-level Ruby market-data service shall exist alongside `backend` and `frontend`.
- The Ruby service is responsible for public crypto market-data retrieval from CoinGecko using Ruby on Rails.
- The provider adapter MAY use the `coingecko_ruby` gem or a thin custom service wrapper around CoinGecko HTTP endpoints, as long as the provider-facing behavior remains isolated inside the Ruby service.
- FastAPI remains the primary authenticated product backend for MarketPulse business workflows.
- The frontend shall not call the Ruby market-data service directly for this public dashboard capability.
- FastAPI shall proxy public market overview requests to the Ruby market-data service and expose the resulting contract through the primary backend API surface.

### 4. First-version data strategy
- The first version shall not add PostgreSQL persistence for prices, charts, coin metadata, or gainers/losers data.
- The first version shall not require scheduled background synchronization.
- Data is fetched on demand from CoinGecko through the Ruby service, subject to free-tier limitations.
- To stay within provider free-tier limits, the public overview shall use a fixed crypto universe based on top assets by market capitalization and avoid duplicate provider fetches within a single request.
- The Ruby microservice shall cache the fully aggregated market-overview payload for one hour before re-fetching upstream provider data.

### 5. Market overview content model
- The initial `Market Overview` tab should support modules for:
  - crypto asset price presentation
  - 24-hour change presentation
  - market cap presentation
  - volume presentation
  - market chart visualization
  - coin information summary
  - top gainers and losers
  - top assets by market capitalization
- The page may compose these modules into cards, tables, or panels as long as the resulting experience remains dashboard-oriented and visually scan-friendly.

### 6. Optional watchlist behavior
- Because the page is public, watchlist content must be additive rather than required.
- If a visitor is not authenticated, the watchlist area should show a neutral empty state or sign-in prompt without blocking the rest of the dashboard.
- If an authenticated user has no saved watchlist data, the page should show an empty state rather than an error.
- Watchlist terminology in future follow-up work should refer to crypto assets rather than stock tickers.

## Security and Failure Handling
- Provider credentials, if required by the chosen CoinGecko access mode, must remain in server-side configuration for the Ruby service.
- The frontend must never call CoinGecko directly.
- The frontend should call only the primary FastAPI backend for public market overview data.
- Browser-facing CORS handling for the dashboard should remain on the primary backend path rather than requiring frontend-to-Ruby-service cross-origin calls.
- Provider failures, malformed responses, and free-tier rate limits should produce safe, user-facing fallback states rather than uncaught errors.
- Because the dashboard is public, rate-limit handling should avoid exposing internal provider details.
- Successful market-overview responses may be served from cache for up to one hour, which means visitors may see slightly stale data in exchange for lower provider usage and better availability.

## API and Client Contract Notes
- The Ruby market-data service owns the provider-facing market overview integration, but the frontend-facing contract is owned by the existing FastAPI backend.
- FastAPI should define explicit request/response schemas for the proxied public market overview payload.
- The frontend should consume the proxied market overview contract through the existing FastAPI OpenAPI and Orval generation workflow.
- This architecture removes the need for frontend-to-provider or frontend-to-Ruby-service CORS configuration in normal dashboard usage.

## Risks and Rollback Considerations
- Risk: a separate Ruby service increases operational complexity for a team that is new to Ruby.
- Mitigation: keep the first version limited to public read-only endpoints and defer persistence/caching.
- Risk: proxying through FastAPI introduces another failure point between the frontend and the Ruby market-data service.
- Mitigation: keep proxy behavior thin, explicitly model upstream failures, and test degraded responses.
- Risk: free-tier provider limits or plan restrictions may make the dashboard feel inconsistent under load.
- Mitigation: limit the initial universe to a top-asset snapshot, avoid duplicate provider calls per request, and specify graceful loading, empty, and error states from the start.
- Rollback: the dashboard shell can remain while the Ruby market-data modules are disabled if the microservice needs to be reverted independently.
