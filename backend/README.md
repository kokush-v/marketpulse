# MarketPulse Backend

## Local Setup

1. Copy the backend environment example:

   ```sh
   cp .env.example .env
   ```

2. Copy the root Docker Compose environment example and start PostgreSQL from the repository root:

   ```sh
   cp ../.env.example ../.env
   docker compose up -d postgres
   ```

3. Install dependencies and run the API:

   ```sh
   uv sync --dev
   uv run uvicorn app.main:app --reload
   ```

The API is available at `http://localhost:8000`. FastAPI documentation is available at
`http://localhost:8000/docs`.

## Make Commands

```sh
make help
make sync
make db-up
make migrate
make dev
```

## Checks

```sh
make lint
make test
make test-db
make check
```

Use `make revision MESSAGE="describe change"` to create an Alembic revision.
