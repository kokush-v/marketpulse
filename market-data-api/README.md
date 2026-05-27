# Market Data API

`market-data-api` is a small Rails API-only service that powers the public MarketPulse crypto dashboard.

## Purpose

- keep provider access on the server side
- provide a single public crypto market overview payload for the frontend dashboard
- degrade safely when the upstream provider is unavailable or rate-limited

## Endpoints

- `GET /up`
- `GET /api/v1/market-overview`
- `GET /api/v1/assets/search`
- `GET /api/v1/news`

## Environment variables

- `COINGECKO_API_KEY` - optional for CoinGecko demo access modes
- `COINGECKO_API_BASE_URL` - optional, defaults to `https://api.coingecko.com/api/v3`
- `COINGECKO_OPEN_TIMEOUT_SECONDS` - optional, defaults to `5`
- `COINGECKO_READ_TIMEOUT_SECONDS` - optional, defaults to `5`
- `COINGECKO_MAX_RETRIES` - optional, defaults to `1`
- `NEWS_API_KEY` - required for NewsAPI-backed coin news search
- `NEWS_API_BASE_URL` - optional, defaults to `https://newsapi.org/v2`
- `MARKET_OVERVIEW_DETAIL_THREADS` - optional, defaults to `4`
- `MARKET_OVERVIEW_SNAPSHOT_FRESH_TTL_SECONDS` - optional, defaults to `3600`
- `MARKET_OVERVIEW_SNAPSHOT_STALE_TTL_SECONDS` - optional, defaults to `21600`
- `MARKET_OVERVIEW_REFRESH_LOCK_TTL_SECONDS` - optional, defaults to `300`
- `REDIS_URL` - required in production for the shared cache backend
- `WEB_CONCURRENCY` - optional Puma worker count for production
- `RAILS_MIN_THREADS` - optional Puma minimum thread count
- `RAILS_MAX_THREADS` - optional Puma maximum thread count

## Ranking universe

The service uses a fixed in-code snapshot of 10 large-cap crypto assets as its dashboard universe.

- featured assets come from the top-ranked entries in that universe
- gainers and losers are derived from that same cached overview payload

This keeps the dashboard live on crypto prices and charts without making the product output depend on frontend configuration, while staying within provider free-tier limits.

## Caching

- successful market overview payloads are stored as reusable snapshots
- production requests prefer reading the latest reusable snapshot instead of rebuilding the full provider payload inline
- development and test may continue using `memory_store`, but production requires a shared Redis cache via `REDIS_URL`
- successful snapshots remain available for stale fallback during transient refresh failures within the configured stale retention window
- `GET /api/v1/news` is fetched on demand and is not cached in v1

## Production refresh flow

- run `bundle exec rake market_overview:refresh` from a scheduler at or under the snapshot freshness interval
- the refresh task rebuilds the reusable snapshot outside the normal request path
- if refresh fails and a previous snapshot exists, the service keeps serving the last successful snapshot
- if no successful snapshot exists yet, the first request may perform a bounded cold-start build and will return a safe upstream failure if that build cannot complete successfully

## Production concurrency

- production request concurrency uses Puma workers and threads configured through `WEB_CONCURRENCY`, `RAILS_MIN_THREADS`, and `RAILS_MAX_THREADS`
- CoinGecko detail fan-out is bounded through `MARKET_OVERVIEW_DETAIL_THREADS`
- upstream CoinGecko requests use explicit open/read timeouts and bounded retry behavior

## Development

```bash
docker compose up -d postgres redis
cd market-data-api
gem install bundler
bundle install
bundle exec rails server -p 3001
```

For a local Redis-backed cache, point `REDIS_URL` to `redis://localhost:6379/0`.

## Tests

```bash
cd market-data-api
bundle exec rails test
```
