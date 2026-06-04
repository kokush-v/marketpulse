## ADDED Requirements

### Requirement: Record Notification History For Scheduled Alert Triggers
The system SHALL create notification-history records when scheduled alert evaluation determines that a user's alert has triggered, including during catch-up processing of missed evaluation windows.

#### Scenario: Scheduled alert trigger creates notification history
- **Given** an authenticated user has an alert that becomes eligible during a scheduled evaluation window
- **When** the system processes that alert trigger
- **Then** the system creates a notification-history record for that trigger

#### Scenario: Catch-up processing creates notification history for a missed window
- **Given** an authenticated user has an alert that became eligible during a missed evaluation window
- **When** catch-up processing reaches that missed window
- **Then** the system creates the corresponding notification-history record without requiring the original window to be rerun manually

### Requirement: Preserve Delivery Outcome Visibility During Catch-Up
The system SHALL preserve observable notification-delivery outcomes for scheduled and catch-up alert processing.

#### Scenario: Telegram delivery succeeds during catch-up
- **Given** an authenticated user has an active Telegram link
- **And** catch-up processing reaches a missed evaluation window where one of the user's alerts triggered
- **When** Telegram delivery succeeds
- **Then** the resulting notification outcome remains visible through the system's notification records or delivery status

#### Scenario: Telegram delivery fails during catch-up
- **Given** an authenticated user has an active Telegram link
- **And** catch-up processing reaches a missed evaluation window where one of the user's alerts triggered
- **When** Telegram delivery fails
- **Then** the resulting failure outcome remains visible through the system's notification records or delivery status
