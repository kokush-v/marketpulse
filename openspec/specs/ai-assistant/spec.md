# ai-assistant Specification

## Purpose
TBD - created by archiving change add-ai-assistant-chat. Update Purpose after archive.
## Requirements
### Requirement: Provide A Protected Web Assistant Conversation

The system SHALL provide authenticated users with a web AI assistant accessible through a product widget and a dedicated protected assistant page. When the widget opens without an active widget conversation, the system SHALL let the user start a new conversation or select one of that user's existing conversations before showing the chat interface.

#### Scenario: Authenticated user opens the widget

- **Given** an authenticated user is on a protected product screen
- **When** the user opens the assistant widget without an active widget conversation
- **Then** the system shows a New conversation action and that user's existing conversations
- **And** the system does not expose conversations owned by another user

#### Scenario: Unauthenticated visitor requests the assistant page

- **Given** a visitor without an authenticated session
- **When** the visitor requests the assistant page
- **Then** the system requires sign-in before granting access

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

### Requirement: Answer Coin Information And News Requests

The system SHALL allow an authenticated user to request a cryptocurrency description, available market information, and latest coin news through the assistant.

#### Scenario: User asks about a coin

- **Given** an authenticated user asks the assistant about a valid coin name or symbol
- **When** relevant market information is available through the established product services
- **Then** the assistant returns a clear coin-oriented response using normalized information

#### Scenario: User asks for coin news

- **Given** an authenticated user asks the assistant for news about a valid coin name or symbol
- **When** the news service returns matching articles
- **Then** the assistant returns a concise response based on the available articles

#### Scenario: Market or news provider is unavailable

- **Given** an authenticated user requests coin information or news through the assistant
- **When** the corresponding provider flow fails, is rate-limited, or returns malformed data
- **Then** the assistant returns a safe recoverable error response
- **And** the response does not expose provider credentials or raw provider internals

### Requirement: Minimize Read Tool Data Exposure

The system SHALL return only user-relevant, compact data from assistant read tools. Read-tool results SHALL not expose internal database identifiers, provider asset identifiers, or redundant provider metadata to the model or through an assistant response.

#### Scenario: User requests a coin overview

- **Given** an authenticated user asks about a supported coin
- **When** the assistant reads its market overview
- **Then** the tool result contains only user-relevant identity, description, price, 24-hour percentage change, and rank data
- **And** it excludes the provider asset identifier, categories, raw market-cap value, and absolute price-change value

#### Scenario: User lists personal records

- **Given** an authenticated user asks the assistant to list watchlist assets or alerts
- **When** the assistant uses the corresponding read tool
- **Then** the result contains user-readable names, symbols, statuses, and summaries as applicable
- **And** it does not include internal asset or alert identifiers

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

### Requirement: Analyze And Render Price Charts In Chat

The system SHALL allow the assistant to retrieve, analyze, and render an interactive price chart for one to five requested cryptocurrencies. Supported periods SHALL be `24h`, `7d`, `30d`, and `1y`, with `7d` used when the user does not specify a period.

#### Scenario: User requests a single-coin chart

- **Given** an authenticated user requests a price chart for one supported coin
- **When** the assistant retrieves chart data
- **Then** the assistant returns a new message with a concise non-advisory analysis
- **And** the message displays an interactive chart for the selected period

#### Scenario: User compares several coins

- **Given** an authenticated user requests a price comparison for two to five supported coins
- **When** the assistant retrieves chart data
- **Then** the returned message displays those coins as separate series on one interactive chart
- **And** the assistant summarizes the observable comparison without investment advice

#### Scenario: User requests a chart revision

- **Given** an assistant message already displays a price chart
- **When** the user requests a changed selection, such as removing one coin or adding another
- **Then** the system creates a new assistant message with a newly generated chart
- **And** the prior chart remains unchanged in conversation history

#### Scenario: Chart request exceeds the supported coin limit

- **Given** an authenticated user requests a chart for more than five coins
- **When** the assistant evaluates the request
- **Then** the assistant asks the user to narrow the selection
- **And** the system does not create a chart from a partial inferred selection

### Requirement: Manage Owned Product Resources Through Bounded Tools

The system SHALL allow the assistant to use explicit validated tools to list personal watchlist assets and alerts, add or remove a personal watchlist asset, and create, update, pause, resume, or delete a personal alert.

#### Scenario: User creates an alert through conversation

- **Given** an authenticated user asks the assistant to create an alert
- **When** the assistant has collected a complete definition matching an existing supported alert scenario
- **Then** the system creates an alert owned by that user
- **And** the assistant reports the resulting alert summary in the conversation

#### Scenario: User omits a required alert setting

- **Given** an authenticated user asks the assistant to create or update an alert
- **When** the request lacks a required or is ambiguous about a supported alert setting
- **Then** the assistant asks for the missing clarification
- **And** the system does not create or update an alert

#### Scenario: User attempts to act on another user's resource

- **Given** an authenticated user requests an assistant action with an alert or watchlist asset owned by another user
- **When** the assistant tool handles the request
- **Then** the system prevents the action according to protected resource rules

### Requirement: Confirm Destructive Assistant Actions In Chat

The system SHALL require an explicit in-chat confirmation before the assistant removes a saved watchlist asset or deletes an alert.

#### Scenario: User requests alert deletion

- **Given** an authenticated user asks the assistant to delete one of the user's alerts
- **When** the assistant resolves one unambiguous owned target
- **Then** the assistant presents a chat confirmation describing that target
- **And** the system does not delete the alert before confirmation

#### Scenario: User confirms a pending destructive action

- **Given** an authenticated user has a current pending chat confirmation for one destructive action
- **When** the user explicitly confirms that action in the conversation
- **Then** the system performs only the confirmed action
- **And** the assistant reports its outcome in chat

#### Scenario: User cancels or lets confirmation expire

- **Given** an authenticated user has a pending destructive action confirmation
- **When** the user cancels it or the confirmation expires
- **Then** the system clears the pending action
- **And** the destructive operation is not performed

### Requirement: Keep Model Access Bounded And Backend-Owned

The system SHALL orchestrate assistant responses through a backend-owned LangGraph flow using Groq and SHALL restrict model actions to the registered assistant tools.

#### Scenario: Model requests a supported tool

- **Given** the assistant determines that it needs product data or a permitted product action
- **When** the LangGraph flow receives a request for a registered tool with valid input
- **Then** the backend executes that tool within the authenticated user's scope

#### Scenario: Model requests an unsupported action

- **Given** the LangGraph flow receives a model request for an unregistered or invalid tool action
- **When** the request is evaluated
- **Then** the system does not perform that action
- **And** the assistant returns a safe response or requests clarification

### Requirement: Describe Assistant Capabilities Without Internal Disclosure

The system SHALL describe assistant capabilities in concise, user-facing product language. It SHALL NOT disclose registered tool names, tool schemas, system or developer prompts, model/provider configuration, API details, backend implementation details, or credentials in an assistant response.

#### Scenario: User asks what the assistant can do

- **Given** an authenticated user asks which tasks the assistant can help with
- **When** the assistant responds
- **Then** it describes supported product workflows in plain language
- **And** it does not reveal registered tool names or implementation details

#### Scenario: User asks for the tool inventory

- **Given** an authenticated user asks to list tools, functions, APIs, or internal capabilities
- **When** the assistant responds
- **Then** it gives a concise product-language summary when useful
- **And** it does not disclose the internal inventory or identifiers

### Requirement: Resist Prompt-Injection And Internal-Disclosure Requests

The system SHALL treat user requests to reveal protected instructions, alter system-level safeguards, impersonate privileged instructions, or perform unsupported actions as untrusted. It SHALL decline the request without echoing protected content and MAY redirect the user to supported product workflows.

#### Scenario: User requests protected instructions

- **Given** an authenticated user asks the assistant to reveal or repeat its system prompt, developer instructions, hidden rules, credentials, or configuration
- **When** the assistant responds
- **Then** it gives a concise refusal
- **And** it does not reveal or quote protected content

#### Scenario: User attempts to override safeguards

- **Given** an authenticated user tells the assistant to ignore prior instructions, adopt a privileged role, or bypass its safeguards
- **When** the assistant responds
- **Then** it does not comply with the override
- **And** it continues to operate within the supported product boundary

#### Scenario: User requests an unsupported action

- **Given** an authenticated user asks the assistant to perform an action outside registered product capabilities
- **When** the assistant responds
- **Then** it clearly states that it cannot perform that action
- **And** it does not claim access to unavailable systems or execute an unregistered action

### Requirement: Preserve Typed Pending-Action Decisions In Conversation History

The assistant SHALL preserve an authenticated user's typed or quick-reply decision for a pending mutation as an ordinary user message in the same conversation.

#### Scenario: Quick reply is recorded as a chat message

- **WHEN** a user chooses an affirmative or negative quick reply for a pending proposal
- **THEN** the client sends it through the standard message-submission path
- **AND** the conversation records it in the same way as manually entered text

#### Scenario: Decision is visible after reopening a conversation

- **WHEN** a user reopens a conversation after confirming or declining a pending proposal
- **THEN** the user can see their decision and the assistant's resulting outcome in the message history

