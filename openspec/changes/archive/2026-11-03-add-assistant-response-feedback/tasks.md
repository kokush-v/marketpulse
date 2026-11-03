## 1. Database

- [x] 1.1 Add the `assistant_message_feedback` SQLAlchemy model with a unique message reference and cascade delete.
- [x] 1.2 Add the Alembic migration with upgrade and downgrade.

## 2. Backend

- [x] 2.1 Add request and response schemas for feedback and the `feedback` field on `AssistantMessageResponse`.
- [x] 2.2 Add repository methods to create feedback and load feedback with conversation messages, scoped by user.
- [x] 2.3 Add service logic: ownership check, assistant-only messages, reason trimming and length limit, duplicate rejection.
- [x] 2.4 Add `POST /assistant/conversations/{conversation_id}/messages/{message_id}/feedback` with documented `201`, `404`, `409`, and `422` responses.

## 3. Backend Tests

- [x] 3.1 Submit positive and negative feedback with and without a reason.
- [x] 3.2 Reject a second submission for the same message with `409`.
- [x] 3.3 Reject feedback on another user's message or conversation with `404`.
- [x] 3.4 Reject feedback on user messages and compaction markers, invalid ratings, and reasons over the limit with `422`.
- [x] 3.5 Return feedback on assistant messages in conversation responses; feedback is removed when the conversation is deleted.

## 4. API Client

- [x] 4.1 Regenerate the Orval client: `docker compose exec -T -e MARKETPULSE_OPENAPI_URL=http://backend:8000/openapi.json frontend npm run generate:api`.

## 5. Frontend

- [x] 5.1 Add thumbs-up and thumbs-down controls under assistant messages in `assistant-chat.tsx`.
- [x] 5.2 Show an inline optional reason input with Submit and Cancel after selecting a rating.
- [x] 5.3 Handle pending, success (read-only submitted rating), error (keep draft), and `409` (refresh) states.
- [x] 5.4 Show the submitted rating for messages that already have feedback after reload.

## 6. Validation

- [x] 6.1 `docker compose exec -T backend uv run alembic upgrade head`.
- [x] 6.2 `docker compose exec -T backend uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest tests/unit`.
- [x] 6.3 `docker compose exec -T frontend npm run lint`, `npm run typecheck`, `npm run build`.
- [x] 6.4 `openspec validate add-assistant-response-feedback --strict`.
