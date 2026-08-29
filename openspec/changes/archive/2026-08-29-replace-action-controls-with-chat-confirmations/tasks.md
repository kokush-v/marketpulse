## 1. Backend confirmation resolution

- [x] 1.1 Add a deterministic resolver for an explicit confirmation or rejection of the current user-owned pending action before LangGraph handles a new message.
- [x] 1.2 Persist the user's typed decision and the resulting assistant outcome as normal conversation messages.
- [x] 1.3 Make the pending-action lifecycle transactional, including rollback and safe retry behavior when execution fails.
- [x] 1.4 Add backend tests for confirmation, rejection, ambiguous messages, ownership isolation, idempotence, and execution failure.

## 2. Assistant UI

- [x] 2.1 Replace pending-action Confirm and Cancel controls with a static readable proposal summary and an instruction to reply in chat.
- [x] 2.2 Add affirmative and negative quick replies that submit ordinary chat messages through the existing send-message flow.
- [x] 2.3 Update frontend tests for typed and quick-reply decisions, loading states, and failure display.

## 3. Validation

- [x] 3.1 Run backend linting and relevant tests through Docker Compose.
- [x] 3.2 Run frontend linting, type checking, and relevant tests through Docker Compose.
- [x] 3.3 Validate the OpenSpec change with `openspec validate replace-action-controls-with-chat-confirmations --strict`.
