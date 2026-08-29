## Summary

Add a conversation picker to the assistant widget so a user can deliberately start a new chat or resume one of their existing conversations when opening it.

## Problem

The widget currently opens directly into a conversation. A user cannot choose whether to preserve prior context or begin a fresh request before the chat interface appears.

## Proposed Solution

When the widget opens without an active conversation selected for that widget session, it will show a compact conversation picker. The picker will provide a clear New conversation action and a list of the authenticated user's existing conversations. Selecting either option opens the standard chat interface.

## Scope

- Add a widget-only conversation picker before displaying the chat.
- Reuse the existing authenticated conversation list and creation flows.
- Allow the user to choose an existing conversation or create a new one.
- Preserve the selected conversation while the widget remains open.

## Non-Goals

- Changing the dedicated assistant page or its conversation-history sidebar.
- Adding conversation search, pagination, renaming, or deletion to the widget picker.
- Changing conversation ownership, persistence, or backend API contracts.

## Impact

- Affected specification: `ai-assistant`.
- Affected implementation area: assistant widget and its composition with the existing chat component.
