## MODIFIED Requirements

### Requirement: Provide A Protected Web Assistant Conversation

The system SHALL provide authenticated users with a web AI assistant accessible through a product widget and a dedicated protected assistant page. When the widget opens without an active widget conversation, the system SHALL let the user start a new conversation or select one of that user's existing conversations before showing the chat interface.

#### Scenario: Authenticated user opens the widget

- **Given** an authenticated user is on a protected product screen
- **When** the user opens the assistant widget without an active widget conversation
- **Then** the system shows a New conversation action and that user's existing conversations
- **And** the system does not expose conversations owned by another user

#### Scenario: User starts a new widget conversation

- **Given** the widget conversation picker is visible
- **When** the user selects New conversation
- **Then** the system creates an owned conversation
- **And** opens the standard widget chat for that conversation

#### Scenario: User resumes a widget conversation

- **Given** the widget conversation picker is visible
- **When** the user selects one of the listed conversations
- **Then** the system opens the standard widget chat with that conversation's recorded messages
- **And** keeps that selection while the widget remains open

#### Scenario: User has no prior widget conversations

- **Given** the widget conversation picker is visible
- **When** the user has no existing conversations
- **Then** the system presents the New conversation action with a clear empty state
