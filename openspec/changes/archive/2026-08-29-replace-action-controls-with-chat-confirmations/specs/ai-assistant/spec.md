## ADDED Requirements

### Requirement: Preserve Typed Pending-Action Decisions In Conversation History

The assistant SHALL preserve an authenticated user's typed or quick-reply decision for a pending mutation as an ordinary user message in the same conversation.

#### Scenario: Quick reply is recorded as a chat message

- **WHEN** a user chooses an affirmative or negative quick reply for a pending proposal
- **THEN** the client sends it through the standard message-submission path
- **AND** the conversation records it in the same way as manually entered text

#### Scenario: Decision is visible after reopening a conversation

- **WHEN** a user reopens a conversation after confirming or declining a pending proposal
- **THEN** the user can see their decision and the assistant's resulting outcome in the message history
