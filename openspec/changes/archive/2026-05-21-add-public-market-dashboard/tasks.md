## 1. OpenSpec validation

- [x] 1.1 Run `openspec validate add-public-market-dashboard --strict` before implementation.

## 2. Ruby crypto market-data microservice foundation

- [x] 2.1 Update the root-level Ruby on Rails market-data microservice to serve crypto market overview data instead of stock market overview data.
- [x] 2.2 Add CoinGecko integration boundaries for public crypto market overview data needed by the first dashboard tab.
- [x] 2.3 Define public API endpoints and response contracts for crypto asset price, 24-hour change, market cap, volume, chart data, coin information, and top gainers/losers.
- [x] 2.4 Ensure provider credentials stay server-side and provider failures or rate limits return backend-safe upstream responses.
- [x] 2.5 Add or preserve a one-hour cache for successful aggregated market overview responses to reduce provider free-tier usage.

## 3. FastAPI proxy foundation

- [x] 3.1 Update backend market overview proxy routes, service logic, and typed schemas for the crypto dashboard contract.
- [x] 3.2 Ensure the FastAPI backend calls the Ruby crypto market-data service instead of duplicating provider logic directly.
- [x] 3.3 Map upstream provider and service failures into stable frontend-safe API responses.

## 4. Frontend dashboard shell

- [x] 4.1 Preserve the public dashboard shell with navigation, header, and content regions that can host future tabs.
- [x] 4.2 Keep the first `Market Overview` tab as the default dashboard view.
- [x] 4.3 Ensure the dashboard shell uses clear loading, empty, and error states for public crypto data modules.

## 5. Frontend crypto market overview experience

- [x] 5.1 Replace stock-oriented presentation modules with crypto asset price, 24-hour change, market cap, and volume modules.
- [x] 5.2 Update chart and coin information modules to fit a crypto-market overview page.
- [x] 5.3 Add top gainers/losers and top-assets-by-market-cap modules fed by the public crypto market-data service.
- [x] 5.4 Keep the optional watchlist section non-blocking and align its terminology with crypto assets for future follow-up work.

## 6. Integration and contracts

- [x] 6.1 Keep frontend integration routed through the FastAPI backend rather than direct requests to the Ruby market-data service.
- [x] 6.2 Regenerate Orval clients for the updated backend crypto market overview contract.
- [x] 6.3 Ensure the public dashboard does not require frontend-to-provider or frontend-to-Ruby-service CORS configuration.

## 7. Tests

- [x] 7.1 Add or update Ruby service tests for successful CoinGecko mapping, cache behavior, and upstream failure handling.
- [x] 7.2 Add or update backend tests for proxy success, upstream failure mapping, and stable public crypto contract behavior.

## 8. Final validation

- [x] 8.1 Run `openspec validate add-public-market-dashboard --strict` after implementation updates.
- [x] 8.2 Run relevant backend, frontend, and Ruby service quality gates during the implementation PR.
