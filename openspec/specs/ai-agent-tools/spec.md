# ai-agent-tools Specification

## Purpose
TBD - created by archiving change add-confirmed-ai-agent-tools. Update Purpose after archive.
## Requirements
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

When an agent proposes a mutation, the system SHALL render a human-readable summary of the proposed change in the conversation and ask the user to explicitly confirm or decline it by replying in chat. The summary SHALL NOT expose tool names, internal identifiers, or separate Confirm and Cancel controls.

#### Scenario: Displaying a mutation proposal

- **WHEN** the agent prepares a mutation proposal
- **THEN** the conversation displays a readable summary of the target and requested change
- **AND** the assistant asks the user to reply with an explicit confirmation or rejection
- **AND** the UI offers affirmative and negative quick replies that send ordinary user messages

### Requirement: Resolve Pending Mutations Safely From Chat

The system SHALL resolve only direct, unambiguous affirmative or negative replies before model invocation. It SHALL not use the language model to interpret a confirmation and SHALL keep an unresolved proposal pending for other messages.

#### Scenario: Ambiguous reply does not execute a mutation

- **WHEN** a user sends a message that is not a direct affirmative or negative reply while a proposal is pending
- **THEN** the system SHALL NOT execute or cancel that proposal solely because of that message
- **AND** the message continues through the normal assistant flow

#### Scenario: A proposal cannot be resolved by another user

- **WHEN** a user attempts to resolve a pending action they do not own
- **THEN** the system SHALL NOT expose, execute, or cancel that action

#### Scenario: Mutation execution fails

- **WHEN** an affirmative reply triggers a mutation that fails
- **THEN** the system rolls back the failed transaction before accessing pending-action state
- **AND** returns a user-safe outcome without falsely marking the mutation complete

