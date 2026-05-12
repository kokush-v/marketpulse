<h1 align="center">MarketPulse</h1>

<p align="center">
  One place to follow crypto and stock markets: prices, charts, news and smart alerts
  that find you on Telegram.
</p>

---

## What is MarketPulse?

Keeping up with the market usually means a dozen tabs: one for prices, one for news,
one for the alert you set on some exchange and forgot. MarketPulse puts it in a single
dashboard. Build your own watchlists, see live prices and history, read the news for
the companies and coins you follow, and get notified on Telegram when something you
care about happens.

It is a pet project, built spec-first with [OpenSpec](https://github.com/Fission-AI/OpenSpec):
every feature starts as a written proposal and ends as code and tests.

## Features

- **Watchlists**: group the tickers you follow and star the ones that matter most
- **Market data**: current prices and historical charts for crypto and stocks
- **News**: articles related to the assets on your lists
- **Alerts**: price rules that are evaluated on a schedule, with control over how
  often they re-trigger
- **Telegram bot**: notifications, daily digests and per-user settings
- **AI assistant**: ask questions about your watchlists and market data in plain language
- **Accounts**: sign-in through Supabase Auth, every user sees only their own data

## How it is built

```
marketpulse/
├── backend/          FastAPI service: auth, watchlists, alerts, Telegram, AI assistant
├── frontend/         Next.js app: dashboard and account screens
├── market-data-api/  Rails service that wraps CoinGecko, Finnhub and the news API
├── k8s/              Kubernetes manifests for every service, Postgres and Redis
└── openspec/         Specs and change proposals that drive development
```

| Layer | Tech |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query |
| Market data | Ruby on Rails, Redis |
| Data sources | CoinGecko, Finnhub, News API |
| Auth | Supabase Auth |
| Infrastructure | Docker Compose for development, Kubernetes for deployment |
| Quality | Pytest, Jest, Rails tests, Ruff, ESLint, GitHub Actions |

## Quick start

```sh
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp market-data-api/.env.example market-data-api/.env

docker compose up --build
```

Then open <http://localhost:3000>. The backend runs on port 8000 and the market-data
service on 3001. You will need your own API keys for the data providers and a
Supabase project, which go into the `.env` files above.

Everything runs inside containers, with source folders mounted so changes reload
automatically. The full list of commands for tests, linting and migrations is in the
[development guide](docs/development.md).

## Project status

Under active development. Watchlists, market data, alerts, the Telegram bot and the
AI assistant are working; the roadmap lives in the OpenSpec changes.
