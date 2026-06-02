## ADDED Requirements

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
