## ADDED Requirements

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
