## ADDED Requirements

### Requirement: Provide A Protected Web Assistant Conversation

The system SHALL provide authenticated users with a web AI assistant accessible through a product widget and a dedicated protected assistant page.

#### Scenario: Authenticated user opens the widget

- **Given** an authenticated user is on a protected product screen
- **When** the user opens the assistant widget
- **Then** the system shows a chat interface for that user's conversation

#### Scenario: Unauthenticated visitor requests the assistant page

- **Given** a visitor without an authenticated session
- **When** the visitor requests the assistant page
- **Then** the system requires sign-in before granting access

### Requirement: Preserve User-Owned Conversations

The system SHALL persist assistant conversations and messages by authenticated user and SHALL not expose one user's conversations to another user.

#### Scenario: User continues a conversation on the dedicated page

- **Given** an authenticated user has exchanged messages through the assistant widget
- **When** the user opens the same conversation on the assistant page
- **Then** the system shows the prior messages in their recorded order

#### Scenario: User requests another user's conversation

- **Given** an authenticated user
- **And** another user owns an assistant conversation
- **When** the authenticated user attempts to retrieve that conversation
- **Then** the system rejects the request according to protected resource rules

### Requirement: Provide Contextual Suggested Replies

The system SHALL persist and display exactly three short, non-empty, distinct suggested replies with every assistant message. Each suggestion SHALL be generated from the assistant response and available conversation context, and SHALL be suitable to submit as the user's next message without further transformation.

#### Scenario: User receives an assistant response

- **Given** an authenticated user sends a message in an assistant conversation
- **When** the assistant produces its response
- **Then** the response includes exactly three contextual suggested replies
- **And** the suggestions are retained with that assistant message in conversation history

#### Scenario: User selects a suggested reply

- **Given** an assistant message displays suggested replies
- **When** the user selects one suggestion
- **Then** the system sends that suggestion through the normal conversation message flow
- **And** the selected text is recorded as the user's message
- **And** the selected assistant message's suggested-reply controls are hidden immediately

### Requirement: Manage Owned Conversation History

The system SHALL allow an authenticated user to rename or delete only that user's assistant conversations from the dedicated conversation history. A conversation entry SHALL expose these actions in a context menu triggered by a right-click.

#### Scenario: User renames a conversation

- **Given** an authenticated user views an owned conversation in the dedicated conversation history
- **When** the user selects Rename from its context menu and saves a non-empty title
- **Then** the system persists and displays the new title for that conversation

#### Scenario: User confirms conversation deletion

- **Given** an authenticated user selects Delete from an owned conversation's context menu
- **When** the user confirms deletion in the inline confirmation state
- **Then** the system deletes that conversation and its associated assistant data
- **And** the deleted conversation is removed from the history

#### Scenario: User cancels conversation deletion

- **Given** an authenticated user has opened the inline deletion confirmation for a conversation
- **When** the user selects Cancel
- **Then** the system keeps the conversation unchanged

#### Scenario: User targets another user's conversation

- **Given** an authenticated user attempts to rename or delete a conversation owned by another user
- **When** the request reaches the backend
- **Then** the system rejects the operation according to protected resource rules

#### Scenario: User renames a conversation without changing its place

- **Given** an authenticated user views a conversation at a particular position in the history
- **When** the user saves a new title for that conversation
- **Then** the history keeps the conversation at the same relative position

### Requirement: Derive An Initial Conversation Title

The system SHALL derive an initial title for a titleless assistant conversation from its first non-empty user message. The title SHALL contain the first three words of that message and SHALL end with `...` when the message contains more than three words. An explicit or subsequently renamed title SHALL be preserved.

#### Scenario: First message contains up to three words

- **Given** an authenticated user has a titleless assistant conversation
- **When** the user sends the first non-empty message containing up to three words
- **Then** the system persists those words as the conversation title

#### Scenario: First message contains more than three words

- **Given** an authenticated user has a titleless assistant conversation
- **When** the user sends the first non-empty message containing more than three words
- **Then** the system persists the first three words followed by `...` as the conversation title

#### Scenario: User has supplied a title

- **Given** an authenticated user has supplied or renamed a conversation title
- **When** the user sends a message in that conversation
- **Then** the system preserves the user-provided title

### Requirement: Use Readable Assistant Response Formatting

The assistant SHALL use concise prose and Markdown lists by default. It SHALL use a Markdown table only when the user requests one or when a comparison of multiple same-shaped records is materially clearer in a table.

#### Scenario: User asks about one coin

- **Given** an authenticated user asks the assistant about a single coin
- **When** the assistant returns a description or market summary
- **Then** the response uses prose or a list as appropriate
- **And** it does not use a Markdown table solely because the tool result is structured

#### Scenario: User compares several records

- **Given** an authenticated user asks to compare multiple coins, alerts, or other same-shaped records
- **When** a table makes their differences easier to scan
- **Then** the assistant may use a concise Markdown table

### Requirement: Keep Model Access Bounded And Backend-Owned

The system SHALL orchestrate assistant responses through a backend-owned LangGraph flow using Groq and SHALL restrict model actions to the registered assistant tools defined by the `ai-agent-tools` capability.

#### Scenario: Model requests a supported tool

- **Given** the assistant determines that it needs product data or a permitted product action
- **When** the LangGraph flow receives a request for a registered tool with valid input
- **Then** the backend executes that tool within the authenticated user's scope

#### Scenario: Model requests an unsupported action

- **Given** the LangGraph flow receives a model request for an unregistered or invalid tool action
- **When** the request is evaluated
- **Then** the system does not perform that action
- **And** the assistant returns a safe response or requests clarification
