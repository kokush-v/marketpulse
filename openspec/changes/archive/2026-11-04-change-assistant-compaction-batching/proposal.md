## Summary

Compact assistant conversations in batches instead of on every message: messages accumulate after each compaction until they exceed the context limits, then everything except the latest exchange is summarized at once and accumulation starts again.

## Problem

The model currently sees a sliding window of the last messages. Once a conversation is longer than the window, every new message pushes older messages out of it, so compaction runs on almost every message. Each run adds an extra model call, which slows replies and spends provider tokens, and adds another "Context compacted" divider, so long conversations fill up with repeated markers.

## Proposed Solution

- Treat the messages recorded after the last compaction as the conversation context the model sees, together with the conversation summary.
- When the user sends a message and the context including the new message exceeds the existing limits (`ASSISTANT_MAX_CONTEXT_MESSAGES`, `ASSISTANT_MAX_CONTEXT_CHARACTERS`), summarize all context messages except the latest user and assistant exchange into the conversation summary, record one compaction marker, and keep the latest exchange verbatim.
- Until the limits are exceeded again, do not compact.
- Raise the default context limits to 30 messages and 40 000 characters, set the default model to `openai/gpt-oss-120b` (131K-token context), and list all assistant settings in `backend/.env.example`.
- Keep the existing summary content rules, pending confirmation handling, marker display, and failure handling.

## Scope

Affected domain: `ai-assistant` (backend only). Primary workflow: a long conversation with the assistant in the widget or on the assistant page.

- compaction trigger and the set of messages that are summarized;
- the messages sent to the model after compaction;
- default context limits and default model in backend settings and `.env.example`;
- backend tests for the new compaction behavior.

## Non-Goals

- adding new settings;
- changing the summary prompt or summary content;
- frontend, API, Orval client, or database schema changes;
- manual compaction triggered by the user.

## Impact

- Backend: `app/features/ai_assistant/service.py` (compaction trigger and model history), `app/core/config.py` and `.env.example` (defaults), and `tests/unit/features/ai_assistant/test_compaction.py`.
- Cost: longer context raises input tokens per request; with the defaults a request stays around 10K context tokens.
- Database: no schema change; the existing `context_summary` and `summarized_through_sequence` fields are reused.
- API, frontend, and Orval client: no changes.
