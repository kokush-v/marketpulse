## 1. Frontend behavior

- [x] 1.1 Update the shared assistant chat rendering logic so contextual suggested-reply controls are visible only for the latest assistant turn that has no later user message in the loaded conversation.
- [x] 1.2 After a user message is successfully submitted through either typed input or a contextual suggested reply, update the rendered conversation so stale controls disappear without waiting for a reload.
- [x] 1.3 Apply the behavior consistently to the assistant widget and dedicated assistant page.

## 2. Verification

- [x] 2.1 Add focused frontend regression coverage for hiding stale suggested replies after a later typed message and after a selected suggestion.
- [x] 2.2 Run the relevant frontend test suite, lint, and typecheck through Docker Compose.
