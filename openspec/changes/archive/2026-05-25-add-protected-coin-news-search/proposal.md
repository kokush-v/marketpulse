## Summary

Add a protected backend `GET /news` endpoint that returns the latest news articles for a requested cryptocurrency query and wire that endpoint into the existing `Related updates` block in the protected watchlist workspace. The first version accepts a coin name or symbol through the `query` parameter, forwards the lookup to the `market-data` microservice, exposes optional article images when available, and does not persist or cache news data.

## Problem

MarketPulse currently describes crypto news as part of the product scope, but it does not yet define a dedicated backend news-search capability or a dedicated watchlist integration that uses such a capability. The watchlist experience is expected to show related news for selected assets, but there is no approved contract for how authenticated users request the latest news by coin name or symbol or how the existing `Related updates` card should source that data.

Without an explicit `news` capability, implementation would risk:

- mixing provider-specific behavior into unrelated market-data or watchlist contracts
- exposing an unclear authentication boundary for coin-news search
- introducing inconsistent frontend integrations without a stable backend API contract

## Proposed Solution

Introduce a focused `news` capability for authenticated users with a protected `GET /news?query=bitcoin` route served by the FastAPI backend and backed by the `market-data` microservice, then connect that route to the existing watchlist `Related updates` card for the selected asset.

This change defines:

- a protected backend endpoint for coin-news search
- search behavior that accepts a coin name or symbol in the `query` parameter
- on-demand provider fetches through the `market-data` microservice, which owns the NewsAPI integration
- a stable response contract for latest matching articles, including optional article image URLs
- safe empty and error outcomes for missing results or upstream provider failures
- watchlist frontend behavior that refreshes the existing `Related updates` card when the selected asset changes

## Scope

Affected domains:

- `news`
- `market-data`
- `watchlists`
- `api-client-generation`

Primary user workflows:

- authenticated user requests the latest news for a coin by name or symbol
- authenticated user selects a saved asset in the watchlist and sees the `Related updates` card refresh from the new `/news` endpoint

In scope:

- protected `GET /news` route
- required `query` parameter for coin name or symbol input
- latest-available news lookup through the `market-data` microservice
- frontend-safe success, empty, and upstream-failure API behavior
- OpenAPI contract updates for frontend client generation
- watchlist frontend integration for the existing `Related updates` card
- loading, empty, and error states for the watchlist news card when `/news` is used
- optional news thumbnails in the watchlist `Related updates` card when the provider returns images

## Non-Goals

- caching provider responses
- persisting news articles in the database
- background syncing or scheduled ingestion of news
- multi-coin filtering in one request
- user-defined news alerts or keyword alerts

## Impact

This change adds the first dedicated `news` domain contract, routes user-facing news lookups through the existing backend-to-`market-data` microservice pattern, and makes the watchlist `Related updates` card depend on that contract. It keeps provider credentials on the service side, preserves authenticated access in the primary backend, and creates a stable API surface that future frontend work can reuse for watchlist and other coin-detail experiences.
