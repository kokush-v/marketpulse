## ADDED Requirements

### Requirement: Propose Personal Watchlist Asset Mutations Through The Assistant

The system SHALL let an authenticated user ask the assistant to add an asset to the user's personal watchlist or remove an owned asset from it. The system SHALL present a clear mutation summary and require explicit in-chat confirmation before performing either operation.

#### Scenario: User proposes adding an asset

- **Given** an authenticated user asks to add a resolvable asset to the personal watchlist
- **When** the assistant has all required information
- **Then** it presents a summary naming the asset and waits for confirmation
- **And** no asset is added before confirmation

#### Scenario: User provides an ambiguous asset target

- **Given** an authenticated user requests a watchlist asset mutation without a resolvable asset target
- **When** the tool evaluates the request
- **Then** the assistant asks a concise follow-up question
- **And** it creates no pending proposal or mutation

#### Scenario: User confirms a watchlist asset mutation

- **Given** an authenticated user has a current pending watchlist proposal in a conversation
- **When** the user explicitly confirms that proposal
- **Then** the system executes only that user's proposed watchlist asset mutation
- **And** reports the result in a new assistant message

### Requirement: Propose Alert Mutations Through The Assistant

The system SHALL let an authenticated user ask the assistant to create, update, pause, resume, or delete an owned alert. The system SHALL present a clear summary of the target and relevant configuration and require explicit in-chat confirmation before performing the operation.

#### Scenario: User proposes an alert creation or update

- **Given** an authenticated user requests a supported alert creation or update with complete valid configuration
- **When** the assistant validates the request
- **Then** it presents the alert rule, asset, timing, and requested change in a readable summary
- **And** no alert mutation occurs before confirmation

#### Scenario: User omits required alert data

- **Given** an authenticated user requests an alert creation or update without all required fields
- **When** the assistant evaluates the request
- **Then** it asks only for the missing or ambiguous information
- **And** creates no pending proposal or mutation

#### Scenario: User confirms an alert mutation

- **Given** an authenticated user has a current pending alert proposal in a conversation
- **When** the user explicitly confirms that proposal
- **Then** the system executes only that user's proposed alert mutation
- **And** reports the outcome in a new assistant message

### Requirement: Protect Proposal Ownership And Lifecycle

The system SHALL scope every mutation proposal to the authenticated user and conversation. A proposal SHALL be executed at most once and SHALL become unusable after confirmation, cancellation, expiry, or supersession.

#### Scenario: User cancels or changes a proposal

- **Given** an authenticated user has a pending mutation proposal
- **When** the user cancels it or submits a different mutation request
- **Then** the prior proposal is cancelled or superseded
- **And** the system performs no mutation for that prior proposal

#### Scenario: User attempts to confirm another user's proposal

- **Given** one user owns a pending mutation proposal
- **When** a different authenticated user attempts to confirm or cancel it
- **Then** the system rejects the request according to protected-resource rules

#### Scenario: User repeats a confirmation

- **Given** an authenticated user has already confirmed a mutation proposal
- **When** the confirmation is submitted again
- **Then** the system does not perform the mutation a second time
- **And** returns a safe resolved-proposal outcome

### Requirement: Render Mutation Summaries In Chat

The system SHALL render each pending mutation as a readable conversational summary with Confirm and Cancel controls attached to the relevant assistant message. User-facing assistant text SHALL describe actions and requested values in natural language and SHALL NOT expose raw tool names, argument names, enum values, action identifiers, or JSON keys.

#### Scenario: User reviews a pending mutation

- **Given** the assistant has created a valid pending mutation proposal
- **When** the assistant response is displayed in the widget or dedicated assistant page
- **Then** the user sees the operation, target, and relevant values in understandable language
- **And** technical values are translated into natural user-facing wording
- **And** can confirm or cancel it without a modal dialog

#### Scenario: Proposal is no longer actionable

- **Given** a pending proposal is expired, cancelled, superseded, or resolved
- **When** its assistant message is displayed
- **Then** the controls are disabled or replaced with an understandable final status
