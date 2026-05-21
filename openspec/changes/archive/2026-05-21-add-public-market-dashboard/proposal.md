## Summary
Add a public crypto market dashboard foundation for MarketPulse, including a reusable dashboard shell, an initial crypto market overview tab, and a dedicated Ruby on Rails microservice to supply public crypto market data through CoinGecko-backed integrations.

## Problem
MarketPulse currently lacks a product dashboard that helps visitors immediately understand the product and browse crypto market information. The current market-data direction is still framed around equities, which no longer matches the project's product direction. There is also no finalized specification for a crypto-focused Ruby microservice and backend proxy flow that can power a visually rich public experience while keeping frontend API integration aligned with the project's FastAPI and Orval workflow.

## Proposed Solution
Update the `market-data` capability for a public dashboard foundation so it standardizes:
- a reusable dashboard shell with navigation, header, and content regions that can host future tabs
- a first public `Market Overview` tab with crypto-oriented UI modules such as asset pricing, 24-hour change, market cap, volume, charts, coin information, and top gainers/losers
- a dedicated Ruby on Rails microservice located alongside `backend` and `frontend`
- server-side CoinGecko-based crypto market integration through the Ruby service so provider credentials and provider-specific behavior remain outside the frontend
- FastAPI proxy endpoints that expose public market overview data to the frontend through the primary backend API surface
- a first-version delivery model that does not require persistence or local historical storage
- a one-hour microservice-side cache for the aggregated public market overview payload to stay within provider free-tier limits
- a free-tier-friendly first-version universe limited to a fixed top crypto snapshot by market capitalization
- graceful handling of optional user watchlist content without making the page private

## Scope
In scope:
- Public dashboard shell behavior and layout expectations for future dashboard tabs
- Public `Market Overview` tab behavior and supported content modules
- Separate Ruby service boundary and its responsibility for CoinGecko-backed public crypto market data
- FastAPI proxy behavior and OpenAPI contracts for public market overview access
- Public frontend access behavior for the dashboard
- Graceful states for missing market data, rate-limited provider responses, and absent user watchlist data
- API and integration expectations between the frontend, FastAPI backend, and the Ruby market-data microservice

## Non-Goals
- Implementing all future dashboard tabs beyond the initial foundation
- Portfolio analytics, exchange workflows, or trading actions
- Persisting prices, charts, or coin metadata in PostgreSQL
- Adding background sync or historical storage for the first version
- Replacing FastAPI as the primary authenticated product backend
- Watchlist creation and management workflows

## Impact
Affected domains:
- `market-data`

Primary user workflows:
- Visitor opens a public market dashboard without authentication
- Visitor browses a market overview tab with visually rich crypto market information
- Authenticated user optionally sees watchlist content when available without changing the dashboard's public access model

System impact:
- Introduces or repurposes a root-level Ruby market-data microservice boundary for crypto data
- Adds a provider-backed market-data service behind the primary backend API surface
- Establishes dashboard layout conventions that future tabs should follow
- Requires OpenAPI and Orval alignment for public market overview contracts
- Defers persistence, caching, and broader product personalization to later changes
