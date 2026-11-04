## 1. Backend

- [x] 1.1 Change the compaction trigger in `AssistantService` to compact only when the messages after the last compaction plus the pending message exceed the context message or character limit.
- [x] 1.2 Summarize all context messages before the latest stored user and assistant exchange, advance `summarized_through_sequence`, and record one compaction marker.
- [x] 1.3 Send the model only the summary, the messages after the last compaction, and the pending message; keep the pending confirmation context and the graph safety bound.

- [x] 1.4 Set defaults in `app/core/config.py` to `assistant_max_context_messages = 30`, `assistant_max_context_characters = 40_000`, and `groq_model = "openai/gpt-oss-120b"`; list `GROQ_MAX_TOKENS`, `ASSISTANT_MAX_CONTEXT_MESSAGES`, and `ASSISTANT_MAX_CONTEXT_CHARACTERS` in `backend/.env.example`.

## 2. Tests

- [x] 2.1 Update `tests/unit/features/ai_assistant/test_compaction.py`: no compaction below the limits, compaction when the message or character limit is exceeded, the latest exchange is retained, no compaction on the next message after a compaction, model input after compaction, and failure handling.

## 3. Validation

- [x] 3.1 Run `docker compose exec -T backend uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest tests/unit`.
- [x] 3.2 Run `openspec validate change-assistant-compaction-batching --strict`.
