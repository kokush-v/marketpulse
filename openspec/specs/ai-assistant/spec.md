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

### Requirement: Show Response Sources Under Assistant Messages

The system SHALL attach to each assistant message the sources of the data returned by the tools used for that response and SHALL display them in a sources block under the message in the assistant widget and page. The sources block SHALL be collapsed by default for any number of sources. The collapsed block SHALL show the `Sources` heading, the unique source labels, and the total number of sources, and SHALL let the user expand it. The expanded block SHALL list every source and SHALL let the user collapse it again. In the expanded list, news sources SHALL include the publisher, article title, publication time, and article link. Price, market, watchlist, and alert data sources SHALL be labeled `MarketPulse knowledge`, SHALL include the data update time when applicable, and SHALL NOT include a link. Stale markers SHALL be shown in the expanded list only. Sources SHALL be persisted with the message.

#### Scenario: User asks for coin news

- **Given** an authenticated user asks the assistant for the latest news about a coin
- **When** the assistant responds using returned news articles
- **Then** the collapsed sources block shows the unique publishers and the number of sources
- **And** after the user expands it, the block lists each used article with its publisher, title, publication time, and a link to the article

#### Scenario: User collapses the sources list

- **Given** the sources block of an assistant message is expanded
- **When** the user collapses it
- **Then** the block again shows only the heading, unique source labels, and the number of sources

#### Scenario: User asks for a coin price

- **Given** an authenticated user asks for the current price of a coin
- **When** the assistant responds using market data
- **Then** the collapsed sources block shows `MarketPulse knowledge` and a count of one
- **And** after the user expands it, the source shows the market data update time and has no link

#### Scenario: Stale source in a collapsed block

- **Given** an assistant message has a source marked as stale
- **When** the sources block is collapsed
- **Then** the stale marker is not shown
- **And** after the user expands the block, the stale marker is shown next to that source

#### Scenario: User asks about personal alerts

- **Given** an authenticated user asks the assistant to list their alerts
- **When** the assistant responds using the user's alert data
- **Then** the sources block shows `MarketPulse knowledge` without a link

#### Scenario: Response uses no data

- **Given** the assistant responds without using any data tool
- **When** the message is displayed
- **Then** no sources block is shown

#### Scenario: User reopens a conversation

- **Given** an assistant message was recorded with sources
- **When** the owning user reopens the conversation
- **Then** the message displays the same sources in a collapsed block

### Requirement: Warn About Stale Market Data

The system SHALL treat market data as stale when its update time is older than a configurable freshness threshold, defaulting to 15 minutes, or when its update time is unknown. When an answer uses stale market data, the assistant SHALL still answer, SHALL warn the user in the response that the data may be outdated, and the corresponding source SHALL be marked as stale.

#### Scenario: Price data is older than the threshold

- **Given** the latest available BTC price was updated 5 hours ago
- **When** an authenticated user asks for the current BTC price
- **Then** the assistant states the available price
- **And** warns that the data is outdated and the actual price may differ
- **And** the source is marked as stale with its update time

#### Scenario: Price data is fresh

- **Given** the latest available BTC price was updated within the freshness threshold
- **When** an authenticated user asks for the current BTC price
- **Then** the assistant answers without a staleness warning
- **And** the source is not marked as stale

### Requirement: Answer Only From Available Data

The assistant SHALL state facts and figures only from tool results available in the conversation. When the tools return no data, return an error, or the question requires information outside MarketPulse data, the assistant SHALL tell the user that it cannot answer instead of answering from unsupported knowledge. The assistant MAY describe MarketPulse capabilities in product language.

#### Scenario: Question outside MarketPulse data

- **Given** an authenticated user asks a general question that no assistant tool can answer, such as what staking is
- **When** the assistant responds
- **Then** it says that it cannot answer that question
- **And** it does not provide an answer from unsupported knowledge

#### Scenario: Tool returns no data

- **Given** an authenticated user asks for news about a coin
- **When** the news tool returns no articles
- **Then** the assistant says that no news is available
- **And** it does not invent articles or links

#### Scenario: User asks what the assistant can do

- **Given** an authenticated user asks which tasks the assistant can help with
- **When** the assistant responds
- **Then** it describes supported MarketPulse workflows in product language

### Requirement: Calculate Market Figures With Deterministic Tools

The system SHALL compute coin-to-USD and USD-to-coin conversions, percentage price changes over `24h`, `7d`, `30d`, or `1y`, and the distance between the current price and a target price using deterministic backend tools rather than the language model. Each result SHALL include the inputs used, including the USD rate or prices and their update times. All calculations SHALL use USD.

#### Scenario: User converts a coin amount to USD

- **Given** an authenticated user asks how many dollars 0.5 BTC is worth
- **When** the assistant responds
- **Then** the conversion is calculated by the backend tool
- **And** the response states the USD amount, the BTC rate used, and its update time

#### Scenario: User converts USD to a coin amount

- **Given** an authenticated user asks how much ETH 1000 USD buys
- **When** the assistant responds
- **Then** the response states the calculated ETH amount and the ETH rate used

#### Scenario: User asks for a percentage change over a period

- **Given** an authenticated user asks how much ETH changed over the last week
- **When** the assistant responds
- **Then** the response states the calculated percentage and USD change with the start and end prices for the `7d` period

#### Scenario: User asks for distance to a target price

- **Given** an authenticated user asks how much BTC must rise to reach 120000 USD
- **When** the assistant responds
- **Then** the response states the current price, the USD difference, and the percentage difference calculated by the backend tool

#### Scenario: Calculation uses stale market data

- **Given** the market data used for a calculation is older than the freshness threshold
- **When** the assistant responds with the result
- **Then** it warns that the data may be outdated
- **And** the calculation source is marked as stale

### Requirement: Calculate Distance To An Owned Price Alert

The system SHALL calculate the distance from the current price to the target of one of the authenticated user's active price alerts. For fixed-price alerts the target SHALL be the alert threshold; for percent alerts the target SHALL be derived from the alert's baseline price and threshold percentage. When several active price alerts match the user's request, the assistant SHALL list them and ask the user to choose before calculating. Alerts owned by other users SHALL NOT be used.

#### Scenario: One matching alert

- **Given** an authenticated user has one active price alert for BTC above 100000 USD
- **When** the user asks how far BTC is from their alert
- **Then** the response states the current price, the alert target, and the USD and percentage distance

#### Scenario: Percent alert

- **Given** an authenticated user has an active alert for ETH rising 5% from a baseline price of 3000 USD
- **When** the user asks how far ETH is from that alert
- **Then** the distance is calculated to a target of 3150 USD

#### Scenario: Several matching alerts

- **Given** an authenticated user has three active price alerts for BTC
- **When** the user asks how far BTC is from their alert
- **Then** the assistant lists the three alerts and asks which one to use
- **And** no distance is calculated until the user chooses

#### Scenario: No active price alert matches

- **Given** an authenticated user has only a news alert for BTC
- **When** the user asks how far BTC is from their alert
- **Then** the assistant says there is no active price alert for BTC
- **And** no distance is calculated

### Requirement: Clarify Missing Calculation Inputs

The assistant SHALL ask a clarification question instead of guessing when a calculation request lacks or has ambiguous required inputs, such as the coin, the amount, the period, or the target.

#### Scenario: Amount is missing

- **Given** an authenticated user asks how many dollars their BTC is worth without giving an amount
- **When** the assistant responds
- **Then** it asks for the BTC amount
- **And** no conversion result is given

#### Scenario: Coin is ambiguous

- **Given** an authenticated user asks for a conversion using a coin name that matches several assets
- **When** the assistant responds
- **Then** it lists the matching coins and asks which one is meant

### Requirement: Decline Unsupported Calculations

The assistant SHALL NOT perform market calculations itself. When a user asks for a calculation that no calculation tool supports, the assistant SHALL say that it cannot calculate it.

#### Scenario: User asks for a historical profit calculation

- **Given** an authenticated user asks how much they would have earned by buying 1 BTC a year ago
- **When** the assistant responds
- **Then** it says that it cannot calculate that
- **And** it does not provide a figure

#### Scenario: User asks for a non-USD conversion

- **Given** an authenticated user asks how many euros 1 BTC is worth
- **When** the assistant responds
- **Then** it says that only USD calculations are supported

### Requirement: Rate Assistant Responses

The system SHALL allow an authenticated user to rate an assistant message in that user's conversation as positive or negative and to optionally provide a free-text reason. The system SHALL store one rating per assistant message and SHALL NOT allow a submitted rating to be changed or removed. Ratings SHALL be available only for assistant messages.

#### Scenario: User rates a response negatively with a reason

- **Given** an authenticated user views an assistant message without a rating
- **When** the user selects the negative rating, enters a reason, and submits
- **Then** the system stores the negative rating and the reason for that message
- **And** the message shows the submitted negative rating

#### Scenario: User rates a response without a reason

- **Given** an authenticated user views an assistant message without a rating
- **When** the user selects the positive rating and submits without a reason
- **Then** the system stores the positive rating without a reason

#### Scenario: User switches rating before submitting

- **Given** an authenticated user has selected the positive rating but not submitted it
- **When** the user selects the negative rating and submits
- **Then** the system stores only the negative rating

#### Scenario: User tries to rate the same message again

- **Given** an assistant message already has a submitted rating
- **When** a second rating for that message reaches the backend
- **Then** the system rejects it
- **And** the original rating is unchanged

#### Scenario: User reopens a conversation

- **Given** an assistant message was rated
- **When** the owning user reopens the conversation
- **Then** the message shows the submitted rating as read-only

#### Scenario: Rating submission fails

- **Given** an authenticated user submits a rating
- **When** the request fails
- **Then** the chat shows an error
- **And** the user's selected rating and reason remain available to retry

### Requirement: Scope Response Ratings To The Owning User

The system SHALL accept a rating only for an assistant message in a conversation owned by the authenticated user and SHALL delete ratings together with their conversation.

#### Scenario: User rates another user's message

- **Given** an authenticated user
- **And** an assistant message in a conversation owned by another user
- **When** the user submits a rating for that message
- **Then** the system rejects the request according to protected resource rules

#### Scenario: User deletes a rated conversation

- **Given** an authenticated user has rated messages in a conversation
- **When** the user deletes the conversation
- **Then** the ratings for its messages are deleted

### Requirement: Compact Long Conversation Context

The system SHALL compact assistant conversation messages that fall outside the recent-message window into a persisted conversation summary generated by the assistant model. The summary SHALL prioritize the coins the user interacted with and SHALL also retain user-stated facts and preferences, decisions made in the conversation, and open questions. Each model request SHALL include the conversation summary when one exists together with the recent messages. Original messages SHALL remain in conversation history.

#### Scenario: Conversation fits the window

- **Given** an authenticated user's conversation has no messages outside the recent-message window
- **When** the user sends a message
- **Then** no compaction is performed

#### Scenario: Conversation exceeds the window

- **Given** an authenticated user's conversation has messages outside the recent-message window that are not yet summarized
- **When** the user sends a message
- **Then** the system updates the conversation summary to cover those messages before the assistant responds
- **And** the full message history remains visible to the user

#### Scenario: User refers to a coin from early in the conversation

- **Given** an authenticated user discussed SOL early in a conversation that has since been compacted
- **When** the user asks "show me the latest news for it"
- **Then** the assistant requests news for SOL

#### Scenario: Summary contains old prices

- **Given** the conversation summary mentions a price discussed earlier
- **When** the user asks for the current price of that coin
- **Then** the assistant obtains current data through its tools instead of reusing the summarized price

### Requirement: Keep Open Confirmations In Context

The system SHALL include the current non-expired pending confirmation of a conversation in every model request for that conversation, even when the message that proposed it is outside the recent-message window. Expired, confirmed, or cancelled actions SHALL NOT be included.

#### Scenario: Proposal message left the window

- **Given** an authenticated user has a pending alert deletion proposal whose message is outside the recent-message window
- **When** the user asks what is waiting for confirmation
- **Then** the assistant describes the pending alert deletion

#### Scenario: Proposal expired

- **Given** a pending proposal in the conversation has expired
- **When** the user sends a message
- **Then** the expired proposal is not presented to the model as pending

### Requirement: Show Compaction In Conversation History

The system SHALL record each compaction as a marker in the conversation history and SHALL display it in the assistant widget and page as a short "Context compacted" divider at the position where compaction happened. Markers SHALL be visible only in the owning user's conversation and SHALL NOT be sent to the model.

#### Scenario: Compaction happens

- **Given** an authenticated user's message triggers compaction
- **When** the conversation is displayed
- **Then** a "Context compacted" divider appears before the newly exchanged messages

#### Scenario: User reopens a compacted conversation

- **Given** a conversation was compacted earlier
- **When** the owning user reopens it
- **Then** the divider is shown at the same position in the history

### Requirement: Continue When Compaction Fails

When generating a conversation summary fails, the system SHALL still respond to the user's message using the previous summary, if any, and the recent messages, SHALL NOT add a compaction marker, and SHALL retry compaction on a later message.

#### Scenario: Summarization call fails

- **Given** a user's message requires compaction
- **And** the summarization request fails
- **When** the assistant handles the message
- **Then** the user receives a normal assistant response
- **And** no compaction marker is added

### Requirement: Show A Typing Indicator While A Reply Is Pending

The assistant chat SHALL show an animated typing indicator, with an accessible status label, while the assistant reply to a sent message is pending. The indicator SHALL be removed when the reply arrives or the request fails.

#### Scenario: User sends a message

- **Given** an authenticated user is in an assistant conversation
- **When** the user sends a message and the reply is pending
- **Then** the chat shows an animated typing indicator below the conversation
- **And** assistive technologies can announce that the assistant is responding

#### Scenario: Reply arrives or request fails

- **Given** the typing indicator is visible
- **When** the assistant reply arrives or the request fails
- **Then** the chat removes the typing indicator

### Requirement: Reveal New Assistant Replies Progressively

The assistant chat SHALL reveal the text of an assistant reply received during the current session progressively, word by word, and SHALL show the reply's attached content (pending action, price chart, sources, rating controls, and suggested replies) only after the text is fully revealed. Messages loaded from conversation history SHALL render immediately without the reveal.

#### Scenario: New reply arrives

- **Given** an authenticated user sent a message in the current session
- **When** the assistant reply arrives
- **Then** the reply text appears progressively word by word
- **And** the attached content of that reply appears after the full text is shown

#### Scenario: User opens an existing conversation

- **Given** an authenticated user has a conversation with recorded messages
- **When** the user opens that conversation
- **Then** all recorded messages and their attached content are shown immediately without the reveal

### Requirement: Respect Reduced Motion For Assistant Chat Animations

When the user's system requests reduced motion, the assistant chat SHALL show the typing indicator without animation and SHALL render new assistant replies and their attached content immediately.

#### Scenario: User prefers reduced motion

- **Given** an authenticated user whose system requests reduced motion
- **When** the user sends a message and the reply arrives
- **Then** the pending state is shown without animation
- **And** the reply text and its attached content appear immediately

