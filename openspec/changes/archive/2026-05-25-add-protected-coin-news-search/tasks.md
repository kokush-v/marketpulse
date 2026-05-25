## 1. Backend

- [x] 1.1 Add a protected FastAPI `GET /news` endpoint in the `news` feature with explicit request and response schemas.
- [x] 1.2 Implement backend news-search service logic that accepts a coin name or symbol query and requests latest articles from the `market-data` microservice on demand.
- [x] 1.3 Normalize `market-data` microservice article data into a stable API response shape without persisting or caching results.
- [x] 1.4 Map missing query input, upstream failures, malformed payloads, and rate-limit/provider errors into frontend-safe API responses.
- [x] 1.5 Extend the `/news` response contract to include optional article image URLs when available.

## 2. Integrations

- [x] 2.1 Add `market-data` microservice support for NewsAPI-backed coin-news search without exposing provider credentials to the frontend or primary backend clients.
- [x] 2.2 Add primary-backend configuration for calling the `market-data` microservice news endpoint and document service-to-service assumptions and operational constraints.
- [x] 2.3 Normalize provider image fields in the `market-data` microservice without requiring images to exist for every article.

## 3. API Client Generation

- [x] 3.1 Update backend OpenAPI output for the new `news` endpoint contract.
- [x] 3.2 Regenerate Orval frontend API client artifacts for the new endpoint.

## 4. Frontend

- [x] 4.1 Update the watchlist `Related updates` card to request news from the protected `/news` endpoint for the selected asset.
- [x] 4.2 Keep the existing watchlist summary and chart behavior unchanged while replacing only the news-source flow.
- [x] 4.3 Add explicit loading, empty, and error states for the watchlist news card when `/news` is in use.
- [x] 4.4 Render article thumbnails in the watchlist news card when `image_url` is present while preserving a clean text-only fallback.

## 5. Tests

- [x] 5.1 Add backend tests for authenticated access, unauthenticated rejection, valid coin-name query handling, and valid symbol query handling.
- [x] 5.2 Add backend tests for empty-result behavior and upstream error mapping from the `market-data` microservice.
- [x] 5.3 Add backend coverage for optional article image URL mapping when practical.
- [x] 5.4 Run `openspec validate add-protected-coin-news-search --strict`.
