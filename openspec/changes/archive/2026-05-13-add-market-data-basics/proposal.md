# Proposal: Add Basic Market Data

## Problem

Users need a first usable market-data experience before watchlists, rules, alerts, or notifications can be meaningful. The application should let an authenticated user look up a ticker, inspect the latest quote, and view a basic daily historical chart while staying compatible with Finnhub free-plan constraints.

## Scope

- Add backend market-data endpoints for ticker lookup, latest quote retrieval, and daily historical price retrieval.
- Integrate Finnhub from the backend only, with provider credentials never exposed to the frontend.
- Normalize requested ticker symbols to uppercase before provider calls, persistence, and responses.
- Display a frontend market-data view where a user can enter a ticker and see quote details plus a daily historical chart when available.
- Add Orval-based frontend API client generation from the backend OpenAPI schema for this feature.
- Store or cache only data that is expected to remain stable for a long period, such as symbol/company metadata and completed daily historical candles.
- Treat current quote data as volatile and avoid long-lived persistent caching for it.
- Handle Finnhub free-plan limitations, rate limits, unavailable historical candles, and provider errors gracefully.
- Add backend tests with provider mocks for successful responses, validation, normalization, unavailable history, and provider failure handling.

## Out of Scope

- Intraday charts or minute-level market data.
- Automatic polling, realtime streaming, WebSocket subscriptions, or background refresh jobs.
- Watchlists, alert rules, notifications, Telegram delivery, and daily digests.
- Paid Finnhub-only features as a hard requirement for the basic quote experience.
- Frontend automated tests for this change.
- Manually maintained frontend API clients for market-data endpoints.
- Investment advice, recommendations, or trading/order placement.

## Acceptance Criteria

- An authenticated user can enter a ticker and retrieve latest quote information through the backend.
- The frontend never calls Finnhub directly and never receives Finnhub API credentials.
- The frontend market-data integration uses an Orval-generated API client or query hooks from the backend OpenAPI contract.
- Ticker symbols are normalized to uppercase consistently.
- The backend can return daily historical data for charts when Finnhub allows it.
- If historical data is unavailable because of plan limitations, rate limits, or provider errors, the frontend shows a non-blocking chart-unavailable state while quote data can still be shown.
- The implementation does not include intraday data.
- Backend tests use mocks instead of real Finnhub calls.
- Backend tests cover successful quote retrieval, symbol normalization, provider errors, rate-limit or access-denied responses, and historical data fallback behavior.

## Related Specs

- `openspec/specs/market-data/spec.md`
- `openspec/specs/development-workflow/spec.md`
