## 1. Database

- [x] 1.1 Add `context_summary` and `summarized_through_sequence` to `assistant_conversations`.
- [x] 1.2 Allow `compaction` as a stored message role.
- [x] 1.3 Add the Alembic migration with upgrade and downgrade.

## 2. Backend

- [x] 2.1 Detect user and assistant messages outside the recent window that are not yet summarized.
- [x] 2.2 Implement incremental summarization with the prioritized summary prompt and persist the result.
- [x] 2.3 Append a `compaction` marker message after each successful compaction.
- [x] 2.4 Assemble model context from the summary, the current non-expired pending action, and the recent messages, excluding markers.
- [x] 2.5 Update the system prompt: summary figures are historical; current data comes from tools.
- [x] 2.6 Continue without compaction when summarization fails and log the failure.
- [x] 2.7 Add `compaction` to `AssistantMessageRole` in the API schema.

## 3. Backend Tests

- [x] 3.1 No compaction while the conversation fits the window.
- [x] 3.2 Compaction summarizes only newly out-of-window messages and advances the summarized sequence.
- [x] 3.3 Model context includes the summary, a pending action outside the window, and the recent messages, and excludes markers and expired actions.
- [x] 3.4 Summarization failure does not fail the user's request and adds no marker.
- [x] 3.5 Compaction markers are returned only in the owning user's conversation and are removed with it.
- [x] 3.6 Eval scenarios: a coin mentioned before compaction is used in a later tool call ("show news for it"); an open proposal outside the window is still recognized.

## 4. API Client

- [x] 4.1 Regenerate the Orval client: `docker compose exec -T -e MARKETPULSE_OPENAPI_URL=http://backend:8000/openapi.json frontend npm run generate:api`.

## 5. Frontend

- [x] 5.1 Render `compaction` messages as a muted "Context compacted" divider in `assistant-chat.tsx` for the widget and page.
- [x] 5.2 Keep suggested-reply visibility based on user and assistant messages only.

## 6. Validation

- [x] 6.1 `docker compose exec -T backend uv run alembic upgrade head`.
- [x] 6.2 `docker compose exec -T backend uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest tests/unit`.
- [ ] 6.3 `docker compose exec -T backend make test-ai-eval`.
- [x] 6.4 `docker compose exec -T frontend npm run lint`, `npm run typecheck`, `npm run build`.
- [x] 6.5 `openspec validate add-assistant-conversation-compaction --strict`.
