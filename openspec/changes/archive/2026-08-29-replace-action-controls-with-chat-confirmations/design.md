## Context

Mutation proposals already require an explicit confirmation, but the UI currently renders Confirm and Cancel controls that call dedicated endpoints. The desired interaction is a single chat surface: the user writes a response or chooses a quick reply that sends one.

## Decision

The normal assistant-message path will resolve a current pending action before LangGraph is invoked.

1. The server identifies at most one actionable proposal owned by the authenticated user in the requested conversation.
2. It normalizes the submitted message and accepts only direct affirmative or negative forms (for example, Ukrainian `так` / `ні` and English `yes` / `no`).
3. An affirmative reply invokes the existing confirmation lifecycle for that proposal; a negative reply cancels it. Other messages do not resolve the proposal and continue through the normal assistant flow.
4. The user's reply and the resulting assistant outcome are stored as ordinary conversation messages.

This keeps the authorization and mutation decision on the server, avoids relying on the model for a security-sensitive interpretation, and prevents the UI from needing a separate action surface.

## UI

The proposal remains visible as a read-only, human-readable summary. Instead of controls on the proposal card, the assistant provides two quick replies. A quick reply uses the same send-message function as manually submitted text, so it has identical history, loading, error, and retry behavior.

## Failure handling

Mutation execution must use a valid transaction boundary. If execution fails, the transaction is rolled back before changing or re-reading pending-action state. The user receives a safe assistant error message and the proposal remains retryable only when doing so cannot duplicate a completed mutation.

## Consequences

- Confirmation works equally from the full assistant page and the widget.
- Existing direct confirmation endpoints may remain for compatibility, but the frontend will not expose them.
- Exact matching intentionally favors safety over convenience; phrases that are not clearly affirmative or negative cannot trigger a mutation.
