## Context

The assistant already has a backend-owned LangGraph flow, user-owned conversations, and persisted pending assistant actions. This change extends that pattern from destructive operations to every supported mutation, so the same review model applies consistently to create, update, pause, resume, and delete actions.

## Tool Boundaries

Tools are request-scoped and receive the authenticated user from backend dependencies. They never accept a user identifier from the model.

Supported proposals:

- add asset to the personal watchlist
- remove an owned asset from the personal watchlist
- create alert
- update alert
- pause alert
- resume alert
- delete alert

The agent uses existing watchlist and alert services for asset resolution, validation, duplicate checks, ownership, and mutation behavior. It does not reproduce business rules inside tool prompts.

## Proposal And Confirmation Flow

1. The model requests a typed mutation tool.
2. The tool validates input and resolves referenced resources within the authenticated user's scope.
3. If required input is missing or ambiguous, the tool returns a compact clarification outcome and creates no pending proposal.
4. If valid, the tool creates a pending proposal containing the action type, owned target reference where applicable, normalized validated input, a human-readable summary, creation time, and expiry.
5. The assistant message exposes the proposal summary and Confirm/Cancel controls.
6. Confirm executes only the current, unexpired proposal belonging to the same user and conversation. Cancel or expiry clears it without mutation.
7. The execution result is persisted as a new assistant message. A confirmation cannot be reused.

Creating a new proposal invalidates any prior pending proposal in that conversation. A confirmation must be explicit and match the currently presented proposal; it must not be inferred from another message or a stale UI control.

## Data Model And Migration

Extend the existing `assistant_pending_actions` model so it represents all supported mutation proposals, rather than only destructive actions. It must retain:

- action type
- authenticated user and conversation ownership
- normalized validated input and target reference
- safe display summary
- pending, confirmed, cancelled, or expired status
- timestamps and expiry

Add a migration for any changed action-type constraint and for any display summary or metadata field required to render a proposal safely. No provider credentials, raw model output, or internal identifiers are exposed to the browser.

## API And Frontend

Conversation message responses expose optional UI-safe pending-proposal metadata. The API does not expose internal target IDs; confirmation requests identify the pending proposal through a server-issued opaque reference or are scoped to the conversation's current pending proposal.

The frontend renders proposal content as a conversational card below the assistant message, with a readable operation label, target, relevant values, and Confirm/Cancel controls. Normal input stays available, but sending a changed request supersedes the existing proposal.

Regenerate the Orval client after endpoint/schema changes.

## Failure And Security

- All ownership checks occur in service/repository queries as well as at route boundaries.
- Invalid model tool arguments, provider failures, validation errors, expired proposals, and duplicate operations produce safe conversational outcomes and perform no mutation.
- Confirm execution is idempotent: an already resolved proposal cannot run a second time.
- Async database and network I/O remains non-blocking.

## Rollout And Rollback

The change is additive. Disabling tool registration prevents new proposals; existing pending proposals naturally expire. The migration rollback restores the original pending-action constraint after unresolved incompatible rows are handled according to the migration plan.
