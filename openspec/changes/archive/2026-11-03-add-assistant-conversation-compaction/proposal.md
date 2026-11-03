## Summary

Support long assistant conversations without losing important context. When a conversation grows beyond the recent-message window, older messages are compacted into a persisted conversation summary that prioritizes the coins the user interacted with, and the assistant receives that summary, the recent messages, and any open confirmation. The chat shows a compaction marker where compaction happened.

## Problem

The assistant currently sends the model only the last 10 messages within a character budget and silently drops everything older. In long conversations the assistant forgets coins, user-stated facts, and decisions from earlier turns, and it can lose track of an open confirmation whose proposal message has fallen out of the window.

## Proposed Solution

- When messages exist that are older than the recent-message window and not yet summarized, the backend generates an updated summary from the previous summary and those messages with a separate model call, and stores it on the conversation.
- The summary prioritizes coins the user interacted with, and also keeps user-stated facts and preferences, decisions made in the conversation, and open questions.
- Each model request receives the conversation summary, the recent messages, and a description of the current non-expired pending confirmation, regardless of the window.
- Each compaction is recorded in conversation history as a compaction marker that the chat renders as a short divider ("Context compacted"); markers are not sent to the model.
- If summarization fails, the response is still produced from the previous summary and the recent messages.

## Scope

Affected domain: `ai-assistant`.

- incremental conversation summarization and persistence;
- model context assembly with summary, recent messages, and pending confirmation;
- persisted compaction markers exposed through the message API and rendered in the widget and assistant page;
- backend tests, eval scenarios, migration, OpenAPI/Orval regeneration.

## Non-Goals

- showing or editing the summary content in the UI;
- cross-conversation or long-term user memory;
- changing the recent-message window size or the pending-action expiry rules;
- deleting or hiding original messages from conversation history;
- using summarized figures as current market data.

## Impact

- Database: conversation summary fields and support for compaction marker messages (Alembic migration).
- API: message role gains a `compaction` value; Orval regeneration and frontend rendering required.
- Backend: an additional Groq call when compaction is needed; context assembly and prompt changes.
