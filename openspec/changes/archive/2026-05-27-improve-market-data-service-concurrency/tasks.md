## 1. OpenSpec validation

- [x] 1.1 Run `openspec validate improve-market-data-service-concurrency --strict` before implementation.

## 2. Ruby market-data service concurrency model

- [x] 2.1 Add explicit production Puma worker and thread configuration for the Ruby `market-data-api` service.
- [x] 2.2 Replace process-local production caching for market overview snapshots with a shared cache strategy suitable for multiple workers or instances.
- [x] 2.3 Refactor public market overview delivery so normal production requests read a reusable snapshot instead of rebuilding the full provider payload on every request.
- [x] 2.4 Define bounded timeout, retry, and upstream concurrency behavior for CoinGecko-backed refresh work.

## 3. Background refresh flow

- [x] 3.1 Add a background job or scheduled refresh path that updates the public market overview snapshot outside the normal request-response cycle in production.
- [x] 3.2 Preserve the last successful snapshot when a refresh attempt fails or hits upstream rate limits.
- [x] 3.3 Document cold-start or cache-miss behavior for environments where no successful snapshot exists yet.

## 4. Backend integration and observability

- [x] 4.1 Preserve the existing FastAPI-to-Ruby integration contract unless implementation discoveries require an approved follow-up change.
- [x] 4.2 Add operational visibility for cache hits or misses, refresh outcomes, upstream latency, and provider failures.
- [x] 4.3 Document the production deployment expectations for shared cache configuration and background refresh execution.

## 5. Tests

- [x] 5.1 Add or update Ruby service tests for snapshot serving, refresh behavior, stale fallback, and upstream failure handling.
- [x] 5.2 Add or update Ruby service tests for bounded concurrency or timeout behavior where practical.
- [x] 5.3 Add or update backend integration tests only if the FastAPI-facing contract or degraded-response behavior changes.

## 6. Final validation

- [x] 6.1 Run `openspec validate improve-market-data-service-concurrency --strict` after implementation updates.
- [x] 6.2 Run relevant Ruby service and backend quality gates during the implementation PR.
