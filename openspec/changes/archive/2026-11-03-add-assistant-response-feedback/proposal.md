## Summary

Let authenticated users rate an assistant response as positive or negative and optionally explain why in free text. Each assistant message can be rated once, the rating is stored in the database, and the chat shows the submitted rating when the conversation is reopened.

## Problem

There is no way to learn which assistant answers users find helpful or wrong. Without feedback, prompt, tool, and model changes cannot be judged against real user experience, and problematic answers cannot be found for review.

## Proposed Solution

- Add thumbs-up and thumbs-down controls under each assistant message in the widget and the assistant page.
- Selecting a rating opens an inline optional free-text reason field with a submit action; the user may switch between thumbs before submitting.
- Submitting stores one feedback record per assistant message, owned by the user, with the rating, optional reason, and time.
- After submission the controls show the submitted rating and cannot be changed or removed.
- Conversation responses include each message's feedback so the state is shown after reload.

## Scope

Affected domain: `ai-assistant`.

- feedback table, model, repository, and migration;
- a protected endpoint to submit feedback for an owned assistant message;
- feedback exposed on assistant message responses;
- rating controls and optional reason input in the assistant chat;
- backend tests and OpenAPI/Orval regeneration.

## Non-Goals

- changing or removing a submitted rating;
- predefined reason categories;
- an admin panel, reports, analytics, or export (planned separately);
- sending feedback to LangSmith or other external services;
- rating user messages, compaction markers, or individual tool results;
- using feedback to change assistant behavior automatically.

## Impact

- Database: new `assistant_message_feedback` table (Alembic migration); deleted with its conversation.
- API: new feedback endpoint and a `feedback` field on assistant message responses; Orval regeneration and frontend updates required.
- Frontend: rating controls in `assistant-chat.tsx`.
