## Overview

This change introduces a dedicated protected `news` feature in the FastAPI backend. The feature exposes `GET /news` for authenticated users and delegates article lookup to the `market-data` microservice, which owns the NewsAPI integration. The watchlist frontend uses that route to populate the existing `Related updates` card for the selected asset. The first version is intentionally narrow: it searches on demand by a single coin query, returns latest normalized articles, and does not cache or persist provider data.

## Authorization And Ownership

- The endpoint is protected and SHALL require a valid authenticated user session.
- The backend SHALL derive the current user from the validated Supabase access token.
- The request SHALL NOT accept any user identifier because access is user-scoped through authentication only.
- No user-owned news data is persisted in this version, so row-level ownership rules do not add new database requirements.

## API Contract Notes

- Route: `GET /news`
- Query parameter: required `query`
- Input meaning: coin name or symbol, for example `bitcoin` or `BTC`
- Response: normalized latest news articles suitable for direct frontend consumption
- Response shape includes an optional article image URL when upstream data provides one
- Empty results: return a successful empty collection rather than an application error when no matching articles are found
- Upstream failures: return a safe backend-defined error response that does not expose provider secrets or raw provider payloads

The FastAPI backend remains the authenticated entry point for frontend clients. The `market-data` microservice is the internal service responsible for provider-facing news retrieval.

Because this introduces a new backend endpoint contract, OpenAPI output and Orval-generated frontend clients must be updated as part of implementation.

## Watchlist Frontend Integration

- The protected watchlist workspace remains the UI entry point for selected-asset news in this change.
- The existing `Related updates` card SHALL query the new protected `/news` endpoint using the selected asset's coin name or symbol.
- Changing the selected asset in the watchlist SHALL refresh the `Related updates` card without altering the summary and chart data flow.
- The watchlist news card SHALL provide explicit loading, empty, and error states while using the new endpoint.
- The watchlist news card SHOULD display an article thumbnail when `image_url` is present and SHOULD gracefully fall back to the current text-only presentation when it is absent.
- This change does not require a new standalone news page or a separate watchlist layout change.

## Provider Integration

- NewsAPI is the provider for the first version of coin-news lookup.
- Provider access SHALL stay inside the `market-data` microservice.
- The primary FastAPI backend SHOULD call the `market-data` microservice through a dedicated client or service adapter rather than embedding service-to-service calls in route handlers.
- The integration SHALL use async HTTP access patterns compatible with the application's async backend rules.
- The `market-data` microservice SHALL assemble the provider request from the user-supplied coin name or symbol query.
- The system SHALL normalize article fields into a stable application response shape so future provider changes do not leak directly to frontend clients.
- The system SHALL treat article images as optional provider data and SHALL NOT fail the whole news item when an image is missing.

## Failure Handling

The system must account for:

- missing or blank `query` input
- provider timeouts
- provider rate limits
- malformed provider payloads
- provider error responses

In all such cases, the primary backend should return frontend-safe outcomes with explicit application-level error handling rather than raw upstream responses.

## Data Model And Persistence

- This version does not add or modify database tables.
- This version does not persist fetched articles.
- This version does not introduce cache storage.

## Risks

- NewsAPI search relevance for short ticker symbols may produce noisy results.
- Free-tier or rate-limit behavior may temporarily reduce endpoint availability.
- Service-to-service failures between the primary backend and `market-data` may affect response availability even when authentication succeeds.
- On-demand fetches may increase response variability compared with cached news flows.

## Rollback

If the integration proves unstable, the feature can be rolled back by removing the protected route and the related service-to-service news integration without requiring database rollback because this change does not persist new data.
