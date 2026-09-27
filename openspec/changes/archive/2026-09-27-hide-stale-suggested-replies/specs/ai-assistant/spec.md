## MODIFIED Requirements

### Requirement: Provide Contextual Suggested Replies

The system SHALL persist and display exactly three short, non-empty, distinct suggested replies with every assistant message. Each suggestion SHALL be generated from the assistant response and available conversation context, and SHALL be suitable to submit as the user's next message without further transformation. The system SHALL display a message's suggested-reply controls only while no later user message is recorded in that conversation.

#### Scenario: User receives an assistant response

- **Given** an authenticated user sends a message in an assistant conversation
- **When** the assistant produces its response
- **Then** the response includes exactly three contextual suggested replies
- **And** the suggestions are retained with that assistant message in conversation history
- **And** the suggested-reply controls are displayed until the user sends a later message in that conversation

#### Scenario: User selects a suggested reply

- **Given** an assistant message displays suggested replies
- **When** the user selects one suggestion
- **Then** the system sends that suggestion through the normal conversation message flow
- **And** the selected text is recorded as the user's message
- **And** the selected assistant message's suggested-reply controls are hidden immediately

#### Scenario: User sends a later typed message

- **Given** one or more assistant messages in a conversation display suggested-reply controls
- **When** the user successfully sends a later typed message in that conversation
- **Then** the system hides the suggested-reply controls for every earlier assistant message in that conversation

#### Scenario: User reloads a continued conversation

- **Given** an assistant conversation contains a user message that follows one or more assistant messages with persisted suggested replies
- **When** the user opens or reloads that conversation
- **Then** the system does not display suggested-reply controls for the earlier assistant messages
