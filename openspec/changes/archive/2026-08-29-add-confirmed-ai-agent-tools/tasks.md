## 1. Pending Proposal Foundation

- [x] 1.1 Define typed proposal, confirmation, cancellation, and result schemas for all supported watchlist and alert mutations.
- [x] 1.2 Extend assistant pending-action persistence and add an Alembic migration for all mutation action types and UI-safe proposal summaries.
- [x] 1.3 Implement repository/service operations to create, supersede, retrieve, cancel, expire, and atomically confirm a user-owned proposal.

## 2. Watchlist Tools

- [x] 2.1 Implement a typed tool to propose addition of an asset to the authenticated user's personal watchlist using existing services.
- [x] 2.2 Implement a typed tool to propose removal of an owned asset from the authenticated user's personal watchlist.
- [x] 2.3 Return concise clarification outcomes when watchlist names, assets, or targets are missing or ambiguous.

## 3. Alert Tools

- [x] 3.1 Implement typed tools to propose alert creation and update using existing alert validation.
- [x] 3.2 Implement typed tools to propose pause, resume, and deletion of an owned alert.
- [x] 3.3 Return concise clarification outcomes when alert configuration or target selection is missing or ambiguous.

## 4. Confirmation And Chat API

- [x] 4.1 Register proposal tools in the LangGraph flow and ensure no mutation runs before explicit confirmation.
- [x] 4.2 Add protected endpoints to confirm or cancel the current owned proposal and return the updated conversation state.
- [x] 4.3 Expose UI-safe pending-proposal metadata in assistant message/conversation schemas and regenerate the Orval client.

## 5. Frontend

- [x] 5.1 Render a readable pending-proposal card with Confirm and Cancel controls below the relevant assistant message.
- [x] 5.2 Submit confirmation/cancellation through generated API hooks and handle loading, expired, superseded, and recoverable-error states.

## 6. Tests And Validation

- [x] 6.1 Add backend tests for tool validation, ownership, clarification outcomes, and compact tool results.
- [x] 6.2 Add backend tests proving every mutation executes only after its matching confirmation and is idempotent after resolution.
- [x] 6.3 Run relevant backend lint and unit tests.
- [x] 6.4 Run relevant frontend lint and type-check commands.
- [x] 6.5 Run `openspec validate add-confirmed-ai-agent-tools --strict`.
- [x] 6.6 Keep mutation tool identifiers and enum values internal while describing their meaning to users in natural language.
