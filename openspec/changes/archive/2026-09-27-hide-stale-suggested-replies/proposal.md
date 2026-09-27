# Summary

Hide contextual suggested-reply controls once a user continues an assistant conversation with a newer message.

## Problem

Suggested replies remain visible beneath older assistant messages after the user has already sent a later message manually. Those controls no longer represent useful next-turn choices and make the conversation visually noisy.

## Proposed Solution

Show contextual suggested replies only while their assistant message is the latest assistant turn without a later user message. Once the user successfully sends a message in the same conversation—whether typed or selected from a suggestion—the UI hides the contextual suggested-reply controls for all earlier assistant messages. The same visibility rule applies when recorded conversation history is loaded.

## Scope

- Update the `ai-assistant` behavior contract for contextual suggested replies.
- Update the assistant chat UI in both the widget and dedicated page to hide stale contextual suggested-reply controls after a later user message is recorded.
- Preserve the existing behavior that selecting a suggested reply hides the controls immediately.
- Add focused frontend regression coverage for stale-control visibility.

## Non-Goals

- Changing how suggested replies are generated, persisted, or submitted.
- Removing suggested-reply data from conversation history or the API.
- Changing pending mutation confirmation behavior.
- Changing conversation ownership, titles, or history management.

## Impact

- Affected domain: `ai-assistant`.
- Affected user flow: continued conversations in the assistant widget and dedicated assistant page.
- No database, backend API, authentication, or generated-client changes are expected.
