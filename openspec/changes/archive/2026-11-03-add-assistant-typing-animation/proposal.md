## Summary

Make assistant replies feel more alive in the web chat: show an animated typing indicator while a response is pending, and reveal a newly received assistant reply progressively, word by word, before its attached content appears.

## Problem

The assistant chat shows a static "Assistant is thinking…" text while waiting, and a full reply appears all at once. The chat feels abrupt compared to common chat interfaces.

## Proposed Solution

- Replace the "Assistant is thinking…" text with an animated three-dot typing indicator that keeps an accessible status label.
- When a new assistant reply arrives in the current session, reveal its text progressively word by word on the client. The backend does not stream, so the full reply is already available; the effect is presentational only.
- Show the reply's attached content (pending action card, price chart, sources, rating controls, suggested replies) after the text reveal finishes.
- Render conversation history loaded from the server instantly, without the reveal effect.
- When the user prefers reduced motion, show the indicator without animation and render replies instantly.

## Scope

Affected domain: `ai-assistant` (frontend only). Primary workflow: sending a message to the assistant in the widget or on the assistant page.

- typing indicator in the assistant chat;
- progressive reveal of newly received assistant replies;
- deferred display of attached message content until the reveal completes;
- reduced-motion handling.

## Non-Goals

- backend response streaming or any API contract change;
- animating user messages, compaction markers, or history messages;
- a user setting to turn the effect on or off;
- animating Telegram bot messages;
- changing assistant reply content or formatting.

## Impact

- Frontend: `features/ai-assistant/components/assistant-chat.tsx` and assistant chat styles in `app/globals.css`.
- Backend, database, API, and Orval client: no changes.
