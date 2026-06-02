# notifications Specification

## Purpose
TBD - created by archiving change add-telegram-notification-bot. Update Purpose after archive.
## Requirements
### Requirement: Record Telegram Alert Notification Outcomes
The system SHALL record Telegram alert notification attempts and outcomes for users who have Telegram delivery enabled through an active Telegram connection.

#### Scenario: Telegram alert notification succeeds
- **Given** an authenticated user has an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger
- **When** the system sends the resulting alert notification to Telegram successfully
- **Then** the system records a Telegram notification outcome with a success status for that user

#### Scenario: Telegram alert notification fails
- **Given** an authenticated user has an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger
- **When** Telegram delivery fails because of an upstream error, malformed request, or unavailable chat destination
- **Then** the system records a Telegram notification outcome with a failure status for that user
- **And** the failure outcome is safe for frontend consumption

### Requirement: Scope Telegram Notification Records To The Linked User
The system SHALL scope Telegram notification records to the user whose alert triggered and whose Telegram account was linked at delivery time.

#### Scenario: User views own notification history
- **Given** an authenticated user has Telegram notification records
- **When** the user requests notification history through protected product behavior
- **Then** the system returns only that user's notification records

#### Scenario: User attempts cross-user notification access
- **Given** an authenticated user
- **And** another user has Telegram notification records
- **When** the authenticated user attempts to access the other user's notification history
- **Then** the system rejects the request according to protected resource rules

### Requirement: Replace The Previous Telegram Test Notification Message
The system SHALL attempt to keep Telegram test notifications tidy by deleting the previously sent Telegram test-notification message for the same linked user before sending a new test notification.

#### Scenario: Previous Telegram test message is deletable
- **Given** a linked user has a previously sent Telegram test-notification message tracked for chat cleanup
- **When** the user requests a new Telegram test notification
- **Then** the system attempts to delete the previous Telegram test-notification message from chat
- **And** the system sends the new Telegram test notification

#### Scenario: Previous Telegram test message cannot be deleted
- **Given** a linked user has a previously sent Telegram test-notification message tracked for chat cleanup
- **When** the user requests a new Telegram test notification
- **And** deletion of the previous Telegram test-notification message fails
- **Then** the system still sends the new Telegram test notification
- **And** the deletion failure does not block the test-notification flow

### Requirement: Preserve Notification History During Telegram Test Message Replacement
The system SHALL preserve stored notification-history records when replacing Telegram test messages in chat.

#### Scenario: Test notification replacement succeeds in chat
- **Given** a linked user requests a new Telegram test notification
- **When** the system deletes the previous test message in Telegram chat and sends the new test notification
- **Then** the system does not require deletion of prior notification-history records from the database

#### Scenario: Test notification replacement falls back after delete failure
- **Given** a linked user requests a new Telegram test notification
- **When** deletion of the previous Telegram test-notification message fails but the new test notification is still sent
- **Then** the system does not require deletion of prior notification-history records from the database

