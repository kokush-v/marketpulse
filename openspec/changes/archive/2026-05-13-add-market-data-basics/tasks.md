# Tasks

## Backend

- [x] Add backend configuration for Finnhub API base URL and API key without exposing secrets to the frontend.
- [x] Implement a Finnhub provider adapter for ticker lookup, latest quote, and daily historical candles.
- [x] Add market-data service logic for symbol normalization, provider error mapping, and stable-data caching decisions.
- [x] Add protected API endpoints for ticker lookup, latest quote, and daily historical chart data.
- [x] Ensure market-data endpoint schemas, tags, operation IDs, and error responses are suitable for OpenAPI client generation.
- [x] Ensure API responses expose stable, frontend-friendly schemas and do not leak provider-specific credentials or raw error payloads.

## Frontend

- [x] Add Orval configuration for generating a frontend API client from the backend OpenAPI schema.
- [x] Add a package script for regenerating the Orval client.
- [x] Exclude generated Orval output from version control so it is regenerated on demand.
- [x] Add a protected market-data view with ticker input/search.
- [x] Show latest quote details including current price, daily change, open, high, low, previous close, and quote timestamp when available.
- [x] Show a daily historical chart when backend history data is available.
- [x] Show loading, empty, validation, provider-error, and chart-unavailable states.
- [x] Use the Orval-generated client or query hooks for market-data backend calls.
- [x] Avoid frontend direct calls to Finnhub.

## Database

- [x] Add persistence or cache tables for stable symbol/company metadata if needed. Not needed for this backend slice; symbol lookup remains on demand without durable caching.
- [x] Add persistence or cache tables for completed daily historical candles if needed. Not needed for this backend slice; daily history remains on demand without durable caching.
- [x] Avoid long-lived persistent caching for volatile latest quote values.

## Tests

- [x] Add backend tests for ticker normalization and request validation.
- [x] Add backend tests for latest quote success using mocked Finnhub responses.
- [x] Add backend tests for daily historical data success using mocked Finnhub responses.
- [x] Add backend tests for Finnhub rate-limit, access-denied, unavailable-data, malformed-response, and network-failure cases.
- [x] Add backend tests proving provider credentials are not exposed through API responses.
