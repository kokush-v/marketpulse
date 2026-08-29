## Summary

Replace button-based confirmation controls for assistant-initiated mutations with confirmations sent as ordinary chat messages. Offer clear affirmative and negative quick replies that send those messages for the user.

## Problem

The current pending-action card exposes implementation-specific Confirm and Cancel controls. This separates a mutation decision from the conversation and makes the flow inconsistent with the assistant-first chat experience.

## Proposed Solution

When the assistant prepares a watchlist or alert mutation, it will show a human-readable summary and ask the user to reply in the chat to confirm or decline it. The UI will offer quick replies such as “Yes, confirm” and “No, cancel”; choosing one will submit the same ordinary user message as typing it manually.

Before invoking the model for a new message, the backend will deterministically recognize explicit affirmative or negative replies for the current pending action in that user-owned conversation. It will execute or cancel only that action, persist the user's reply and the result in conversation history, and leave ambiguous messages unresolved.

## Scope

- Replace interactive pending-action Confirm and Cancel controls with a static proposal summary and in-chat instructions.
- Add positive and negative quick replies for a pending proposal.
- Resolve explicit typed confirmations and rejections without asking the model to interpret them.
- Preserve authorization, ownership, idempotence, and a safe failure path for pending mutations.

## Non-Goals

- Changing what mutations the assistant can propose.
- Adding a modal or a separate confirmation screen.
- Interpreting ambiguous confirmations through the language model.
- Changing the database schema or the public API contract unless implementation proves it necessary.

## Impact

- Affected specifications: `ai-agent-tools`, `ai-assistant`.
- Affected implementation areas: assistant message handling, pending-action service lifecycle, assistant chat rendering, and tests.
