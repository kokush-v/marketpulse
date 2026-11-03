## Context

Assistant routes live under `/assistant` in `app/features/ai_assistant/routes.py`; messages belong to conversations owned by a user. Conversation responses return `AssistantMessageResponse` items, rendered by `frontend/features/ai-assistant/components/assistant-chat.tsx` for both the widget and the assistant page.

## Decisions

### Data model

Table `assistant_message_feedback`:

- `id` UUID primary key;
- `message_id` FK to `assistant_messages.id`, `ON DELETE CASCADE`, unique (one feedback per message);
- `user_id` FK to `users.id`;
- `rating` enum-like string: `positive` or `negative`;
- `reason` nullable text, trimmed, max 1 000 characters, empty stored as null;
- `created_at` timestamp.

The table is designed for a later admin panel to query by rating and time; no admin access is added now.

### Endpoint

`POST /assistant/conversations/{conversation_id}/messages/{message_id}/feedback`

- Request: `{ "rating": "positive" | "negative", "reason": string | null }`.
- Response `201`: the stored feedback (`rating`, `reason`, `created_at`).
- `404` when the conversation or message does not exist or is not owned by the authenticated user (ownership enforced in the query).
- `422` when the message is not an assistant message, the rating is invalid, or the reason exceeds the limit.
- `409` when feedback already exists for the message.

Business logic lives in the service; the route stays thin.

### Message response

`AssistantMessageResponse` gains `feedback: AssistantMessageFeedbackResponse | null`, populated for assistant messages that have feedback. Loaded with the conversation messages without per-message queries.

### Frontend

Under each assistant message (not user messages or compaction markers):

- thumbs-up and thumbs-down buttons;
- selecting one highlights it and shows an inline optional reason textarea with Submit and Cancel; the user can switch thumbs before submitting;
- Submit calls the generated Orval mutation, shows a pending state, and on success replaces the controls with the submitted rating (read-only) and updates the conversation query cache;
- on error, shows an inline error and keeps the draft for retry; a `409` refreshes the conversation to show the existing rating.

Reason text is user content: rendered as plain text, never as Markdown or HTML.

## Risks

- Accidental submissions cannot be undone; the two-step select-then-submit flow reduces this.

## Rollback

Hide the controls and drop the table with the down migration; no other data depends on it.
