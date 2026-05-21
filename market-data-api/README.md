# Market Data API

`market-data-api` is a small Rails API-only service that powers the public MarketPulse crypto dashboard.

## Purpose

- keep provider access on the server side
- provide a single public crypto market overview payload for the frontend dashboard
- degrade safely when the upstream provider is unavailable or rate-limited

## Endpoints

- `GET /up`
- `GET /api/v1/market-overview`

## Environment variables

- `COINGECKO_API_KEY` - optional for CoinGecko demo access modes
- `COINGECKO_API_BASE_URL` - optional, defaults to `https://api.coingecko.com/api/v3`

## Ranking universe

The service uses a fixed in-code snapshot of 10 large-cap crypto assets as its dashboard universe.

- featured assets come from the top-ranked entries in that universe
- gainers and losers are derived from that same cached overview payload

This keeps the dashboard live on crypto prices and charts without making the product output depend on frontend configuration, while staying within provider free-tier limits.

## Caching

- successful `GET /api/v1/market-overview` payloads are cached in the microservice for 1 hour
- the cache is kept in-process through Rails `memory_store`

## Development

```bash
cd market-data-api
gem install bundler
bundle install
bundle exec rails server -p 3001
```

## Tests

```bash
cd market-data-api
bundle exec rails test
```
