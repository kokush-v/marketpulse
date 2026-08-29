## 1. Backend Foundation

- [x] 1.1 Add the `ai-assistant` feature structure, protected dependencies, typed schemas, domain exceptions, and configuration for the backend-only Groq client.
- [x] 1.2 Add SQLAlchemy models and an Alembic migration for user-owned assistant conversations, messages, and pending destructive actions.
- [x] 1.3 Implement repositories/services that enforce authenticated ownership for conversation retrieval and mutation.
- [x] 1.4 Implement the LangGraph conversation orchestration with bounded Groq inference/tool loops and safe provider failure handling.
- [x] 1.5 Persist exactly three validated model-generated suggested replies with each assistant message and expose them through the conversation API.
- [x] 1.6 Add protected user-owned conversation title update and deletion service/repository operations.
- [x] 1.7 Derive an initial title from a conversation's first user message while preserving an explicit user-provided or renamed title.
- [x] 1.8 Preserve conversation activity ordering when a user renames its title.
- [x] 1.9 Add response-formatting guidance that prevents unnecessary Markdown tables.
- [x] 1.10 Add typed assistant message chart payload persistence and an Alembic migration.

## 2. Assistant Tools

- [x] 2.1 Implement typed read tools for coin overview, coin news, watchlist assets, and alerts by reusing existing domain services.
- [x] 2.5 Minimize read-tool outputs by removing internal identifiers and redundant metadata not needed for an assistant response.
- [ ] 2.2 Implement typed action tools for adding a watchlist asset and creating, updating, pausing, and resuming an owned alert through existing validation and services.
- [ ] 2.3 Implement destructive watchlist-removal and alert-deletion tools with persisted in-chat confirmation, cancellation, expiration, and ownership checks.
- [ ] 2.4 Ensure tools ask for missing or ambiguous required action data rather than making unsupported assumptions.
- [x] 2.6 Add a bounded price-chart data tool supporting one to five coins and the approved periods.

## 3. API And Frontend

- [x] 3.1 Add protected conversation list, create, retrieve, and message endpoints with explicit OpenAPI schemas.
- [x] 3.2 Regenerate the Orval frontend API client after the assistant API contract is available.
- [ ] 3.3 Add the authenticated assistant widget with message composer, loading/error states, and in-chat pending confirmation controls.
- [x] 3.4 Add the protected dedicated assistant page with conversation history and the same chat interaction model.
- [x] 3.5 Render three contextual suggested-reply controls below each assistant message and send the selected text through the standard chat flow.
- [x] 3.6 Add protected conversation rename and delete endpoints, then regenerate the Orval client.
- [x] 3.7 Add a shadcn context menu to conversation history with inline rename and delete confirmation controls.
- [x] 3.8 Collapse an assistant message's quick-reply controls after one of its replies is selected.
- [x] 3.9 Add protected market-history retrieval, regenerate the assistant API client, and render interactive chart cards in assistant messages.

## 4. Tests And Validation

- [ ] 4.1 Add backend tests for conversation ownership, message persistence, read-tool normalization, and safe Groq/domain provider failures.
- [ ] 4.2 Add backend tests for action-tool validation and ownership, including cross-user targets.
- [ ] 4.3 Add backend tests proving destructive actions execute only after the matching in-chat confirmation and do not execute after cancellation or expiration.
- [x] 4.4 Run relevant backend lint and unit tests.
- [x] 4.5 Run relevant frontend lint and type-check commands.
- [x] 4.6 Run `openspec validate add-ai-assistant-chat --strict`.
- [x] 4.7 Add focused backend tests for conversation rename, deletion, and cross-user ownership protection.
- [x] 4.8 Add focused backend tests for automatically derived conversation titles.
- [ ] 4.9 Add focused regression coverage for title-renaming order and quick-reply collapse behavior where practical.
- [x] 4.10 Add focused tests proving read-tool results do not expose internal resource identifiers.
- [x] 4.11 Add focused regression coverage for the response-formatting guidance.
- [x] 4.12 Add backend and frontend coverage for chart data validation, assistant-message chart persistence, and chart-card rendering.
