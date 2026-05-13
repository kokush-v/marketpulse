# Design: Basic Market Data

## Overview

The basic market-data feature introduces backend-mediated access to Finnhub for ticker lookup, latest quotes, and daily historical chart data. The backend remains the trusted boundary for provider credentials, normalization, provider error handling, and caching decisions.

The first version should prioritize a reliable quote experience. Daily charts are supported when available from Finnhub, but the product must degrade gracefully when historical candles are unavailable because of free-plan limitations, rate limits, or provider errors.

## Data Model Changes

The implementation may add persistence or cache tables for data that is expected to remain stable for a long period:

- Symbol or company metadata, such as ticker, display name, exchange, currency, and provider identifiers.
- Completed daily historical candles, keyed by symbol, date, and resolution.

Latest quote values are volatile and should not be treated as long-term stable data. If short-lived request coalescing or temporary caching is introduced to protect the provider limit, it should be clearly bounded and should not be confused with durable historical storage.

## API Changes

The backend should expose protected MarketPulse API routes similar to:

- `GET /api/market-data/symbols/search?query=<query>` for ticker lookup.
- `GET /api/market-data/symbols/{symbol}/quote` for latest quote details.
- `GET /api/market-data/symbols/{symbol}/history?range=<range>&resolution=D` for daily historical chart data.

Responses should use frontend-friendly schemas rather than leaking raw Finnhub payloads. Symbols should be normalized to uppercase in responses.

Historical data should be daily only. Intraday resolutions are out of scope.

Market-data endpoint schemas, tags, operation IDs, and documented error responses should be stable enough for OpenAPI client generation.

## Frontend API Client Generation

The frontend should use Orval to generate API client code from the backend OpenAPI schema. The generated code may include typed request functions and TanStack Query hooks, depending on the final Orval configuration chosen during implementation.

Market-data UI code should call the generated client or generated query hooks instead of hand-written Axios functions for the market-data endpoints. This keeps frontend contracts aligned with FastAPI/Pydantic response schemas and reduces manual drift between backend and frontend.

Generated Orval output should not be committed to the repository. Developers should regenerate it with a package script when the backend OpenAPI contract changes, and generated files should not be edited manually.

## Background Job Changes

No background jobs are included in this change. Market data is fetched on demand.

## Integration Changes

Finnhub is the initial provider for quotes and daily historical candles. The integration should:

- Use server-side credentials only.
- Map provider rate-limit responses to controlled API responses.
- Map access-denied or unavailable historical data responses to a chart-unavailable state.
- Handle malformed provider responses and network failures.
- Avoid making frontend code dependent on Finnhub-specific response shapes.

## Security Considerations

All market-data endpoints are protected for authenticated users. Although basic ticker market data is not user-owned, the routes should still follow the product's authenticated-user model.

The backend must never expose Finnhub API keys, tokens, provider secret configuration, or raw provider error payloads. The frontend must call only the MarketPulse backend.

## Failure Handling

Expected failure cases include:

- Invalid or unsupported ticker symbol.
- Provider rate limit.
- Provider access denied for historical candles.
- Provider outage or network timeout.
- Malformed or incomplete provider response.
- Missing server-side provider configuration.

Quote failures should produce a controlled unavailable state. Historical chart failures should not prevent quote data from rendering when quote data is available.

## Open Questions

- Which exact frontend route should own the market-data search and detail view?
- Should symbol lookup be required before quote retrieval, or should direct ticker entry be enough for the MVP?
- Which daily history ranges should be offered first, such as `1M`, `3M`, and `1Y`?
