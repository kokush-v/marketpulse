## MODIFIED Requirements

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

#### Scenario: Successful test send updates future cleanup state
- **Given** a linked user requests a Telegram test notification
- **When** the system sends the new Telegram test notification successfully
- **Then** the system persists the new Telegram message identifier for that linked user
- **And** the next Telegram test notification request can use that persisted identifier for chat cleanup

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

#### Scenario: Successful test send remains visible for cooldown enforcement
- **Given** a linked user requests a Telegram test notification
- **When** the system sends the new Telegram test notification successfully
- **Then** the resulting test notification attempt remains stored for that user
- **And** a follow-up request inside the cooldown window is rejected according to the per-user cooldown rules
