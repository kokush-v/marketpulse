## Summary

Add confirmed AI-agent tools that let an authenticated user manage personal watchlists and alerts through the assistant chat.

## Problem

The assistant currently provides read-only market and user-resource information. Users cannot safely complete common MarketPulse workflows—such as creating a watchlist, adding an asset, or configuring an alert—without leaving the conversation. Mutations also need an explicit, understandable review step so an agent cannot make an unintended change from incomplete or ambiguous language.

## Proposed Solution

Introduce a focused `ai-agent-tools` capability containing typed, authenticated tools for supported watchlist and alert operations. The agent collects and validates the required data, presents a human-readable summary of every proposed mutation in chat, and executes it only after the user explicitly confirms that exact proposal.

## Scope

Affected domains:

- `ai-agent-tools` (new)
- `ai-assistant`
- `watchlists`
- `alerts`
- `api-client-generation`

Primary workflows:

- add an asset to the personal watchlist or remove an owned asset from it
- create, edit, pause, resume, or delete an owned alert
- ask concise follow-up questions for incomplete or ambiguous requests
- review a plain-language mutation summary and confirm or cancel it in chat
- receive the result as a new assistant message after the confirmed operation runs

Every mutation requires an in-chat confirmation. Read-only tools remain outside this change.

## Non-Goals

- market-data, news, chart, Telegram, notification-setting, or trading operations
- changing existing watchlist or alert validation rules
- automatic confirmation based on natural-language similarity, silence, or a previous confirmation
- batch operations across multiple watchlists or alerts
- changing the dedicated watchlist or alert UI

## Impact

The backend adds request-scoped mutation tools, persisted pending proposals, ownership-safe execution, and protected API metadata for chat confirmation controls. The frontend renders a compact, clear proposal summary and Confirm/Cancel actions in the assistant conversation. Existing watchlist and alert services remain the authoritative validation and mutation layer.
