## ADDED Requirements

### Requirement: Provide Compact Read Tools

The system SHALL provide explicit read tools for coin overview, coin news, user watchlist assets, and user alerts. Tool results SHALL contain only compact user-relevant fields and SHALL not expose internal database identifiers, provider asset identifiers, credentials, or redundant provider metadata.

#### Scenario: User asks about a coin

- **Given** an authenticated user asks the assistant about a valid coin name or symbol
- **When** the overview or news tool obtains data through established services
- **Then** the assistant returns a clear normalized response

#### Scenario: User lists personal records

- **Given** an authenticated user asks to list saved assets or alerts
- **When** the corresponding read tool runs
- **Then** the result contains user-readable labels and summaries without internal identifiers

#### Scenario: A provider is unavailable

- **Given** a read tool requires an unavailable, rate-limited, or malformed provider response
- **When** the tool handles the provider failure
- **Then** it returns a safe recoverable result without provider internals

### Requirement: Retrieve And Render Chart Data Through A Tool

The system SHALL provide a `get_price_chart_data` tool for one to five requested cryptocurrencies. It SHALL accept `24h`, `7d`, `30d`, or `1y`, defaulting to `7d`; resolve provider identifiers internally; and return only user-facing series labels and normalized time/price points for chart rendering.

#### Scenario: User requests a chart

- **Given** an authenticated user requests a chart for one to five supported coins
- **When** the tool retrieves historical data
- **Then** the assistant returns a factual non-advisory analysis and its message displays the resulting interactive chart

#### Scenario: User revises a chart

- **Given** an assistant message already displays a chart
- **When** the user changes the requested coin selection or period
- **Then** the assistant creates a new message and chart while prior charts remain unchanged

#### Scenario: Chart selection needs clarification

- **Given** a request includes more than five coins or an ambiguous coin name or symbol
- **When** the tool validates the request
- **Then** the assistant asks the user to narrow or clarify the selection without creating a partial chart

### Requirement: Safely Manage Owned Resources Through Tools

The system SHALL use explicit validated tools for user-owned watchlist and alert operations. Tools SHALL derive the user from authenticated context, ask for missing or ambiguous required data, and prevent cross-user access.

#### Scenario: User requests a valid owned-resource action

- **Given** an authenticated user provides a complete supported alert or watchlist request
- **When** the corresponding tool executes
- **Then** it changes only that user's resource and reports the result in chat

#### Scenario: User request lacks required data or targets another user

- **Given** an action request is incomplete, ambiguous, or targets an unowned resource
- **When** the tool evaluates it
- **Then** it requests clarification or rejects the operation without mutation

### Requirement: Confirm Destructive Tool Actions In Chat

The system SHALL require explicit in-chat confirmation before a tool removes a saved watchlist asset or deletes an alert.

#### Scenario: User confirms a destructive action

- **Given** the assistant has an unexpired pending destructive action for an unambiguous owned target
- **When** the user explicitly confirms that action
- **Then** the tool performs only the confirmed operation and reports its outcome

#### Scenario: User cancels or lets a confirmation expire

- **Given** an assistant has a pending destructive action
- **When** the user cancels it or it expires
- **Then** the system clears the pending action without mutation
