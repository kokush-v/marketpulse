# MarketPulse: development guide

MarketPulse is an OpenSpec-driven web application for authenticated users to track stock watchlists, market data, alerts, and Telegram notifications.

## Foundation Setup

Copy local environment defaults for each runtime:

```sh
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp market-data-api/.env.example market-data-api/.env
```

Start the complete local development stack:

```sh
docker compose up --build
```

Open the application at <http://localhost:3000>. Docker exposes the backend at
<http://localhost:8000> and the market-data API at <http://localhost:3001>.

Source directories are mounted into their development containers. Updating a
backend Python file restarts Uvicorn automatically; updating a frontend file
refreshes Next.js automatically. Rails reloads changed market-data API code in
development mode.

View all service logs or stop the stack:

```sh
docker compose logs -f
docker compose down
```

Start isolated local test PostgreSQL when running database smoke checks:

```sh
docker compose --profile test up -d postgres-test
```

The test database uses in-memory container storage and is discarded when the
test database container stops.

## Container-Only Commands

All application code and verification commands run inside the Compose
containers. Do not start project services or package managers directly on the
host.

```sh
# Backend
docker compose exec -T backend uv run ruff check .
docker compose exec -T backend uv run pytest tests/unit
docker compose exec -T backend uv run alembic upgrade head

# Frontend
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run test

# Rails market-data API
docker compose exec -T market-data-api bundle exec rails test
```

## Foundation Checks

Backend:

```sh
docker compose exec -T backend uv run ruff check .
docker compose exec -T backend uv run pytest tests/unit
```

Frontend:

```sh
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run build
```

Docker Compose:

```sh
docker compose config
docker compose --profile test config
```

OpenSpec:

```sh
openspec validate setup-project-foundation --strict
```

## Local Pre-Commit Hooks

Install the repository hook tooling once from the repository root:

```sh
npm install
```

The local Git `pre-commit` hook runs:

- backend lint inside the `backend` container
- frontend lint inside the `frontend` container

Both checks run against the full backend/frontend codebases, and either failure blocks the commit.
