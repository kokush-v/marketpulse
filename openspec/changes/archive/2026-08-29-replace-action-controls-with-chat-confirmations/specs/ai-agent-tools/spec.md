## MODIFIED Requirements

### Requirement: Render Mutation Summaries In Chat

When an agent proposes a mutation, the system SHALL render a human-readable summary of the proposed change in the conversation and ask the user to explicitly confirm or decline it by replying in chat. The summary SHALL NOT expose tool names, internal identifiers, or separate Confirm and Cancel controls.

#### Scenario: Displaying a mutation proposal

- **WHEN** the agent prepares a mutation proposal
- **THEN** the conversation displays a readable summary of the target and requested change
- **AND** the assistant asks the user to reply with an explicit confirmation or rejection
- **AND** the UI offers affirmative and negative quick replies that send ordinary user messages

## ADDED Requirements

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
