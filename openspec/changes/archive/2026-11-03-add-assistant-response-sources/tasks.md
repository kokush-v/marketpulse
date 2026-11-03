## 1. Database

- [x] 1.1 Add a nullable JSONB `sources` column to `assistant_messages` in the SQLAlchemy model.
- [x] 1.2 Add the Alembic migration with upgrade and downgrade.

## 2. Backend

- [x] 2.1 Add the `ASSISTANT_MARKET_DATA_MAX_AGE_SECONDS` setting (default 900) and document it in `backend/.env.example`.
- [x] 2.2 Add the source entry contract and a `SourcesCapture` collected per response, with deduplication.
- [x] 2.3 Add source metadata and staleness to `get_coin_overview`, `get_price_chart_data`, and `get_coin_news` results and captured sources.
- [x] 2.4 Add `MarketPulse knowledge` sources to `list_watchlist_assets` and `list_alerts`.
- [x] 2.5 Expose captured sources from the graph response, persist them on the assistant message, and return them in `AssistantMessageResponse.sources`.
- [x] 2.6 Extend the system prompt with tool-grounded answering, stale-data warnings, and the cannot-answer rule.

## 3. Backend Tests

- [x] 3.1 Unit tests for source capture per tool, deduplication, and no source on tool errors or empty results.
- [x] 3.2 Unit tests for staleness: fresh data, data older than the threshold, unknown update time.
- [x] 3.3 Tests that sources are persisted and returned for the owning user's conversation and that responses without tool calls return an empty list.
- [x] 3.4 Add eval scenarios: stale price question, unsupported general-knowledge question triggers no tool, news question calls the news tool.

## 4. API Client

- [x] 4.1 Regenerate the Orval client: `docker compose exec -T -e MARKETPULSE_OPENAPI_URL=http://backend:8000/openapi.json frontend npm run generate:api`.

## 5. Frontend

- [x] 5.1 Render the sources block under assistant messages in `assistant-chat.tsx` (label, title, time, stale marker, news link opening in a new tab).
- [x] 5.2 Render no block for messages without sources, including existing persisted messages.

## 6. Validation

- [x] 6.1 `docker compose exec -T backend uv run alembic upgrade head`.
- [x] 6.2 `docker compose exec -T backend uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest tests/unit`.
- [x] 6.3 `docker compose exec -T backend make test-ai-eval`.
- [x] 6.4 `docker compose exec -T frontend npm run lint`, `npm run typecheck`, `npm run build`.
- [x] 6.5 `openspec validate add-assistant-response-sources --strict`.
