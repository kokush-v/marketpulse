## MODIFIED Requirements

### Requirement: Record Notification History For Scheduled Alert Triggers
The system SHALL create notification-history records when scheduled alert evaluation determines that a user's alert has triggered, including during catch-up processing of missed evaluation windows.

#### Scenario: Scheduled alert trigger creates notification history
- **Given** an authenticated user has an alert that becomes eligible during a scheduled evaluation window
- **When** the system processes that alert trigger
- **Then** the system creates a notification-history record for that trigger

#### Scenario: Multiple recurring triggers on the same day create separate history records
- **Given** an authenticated user has a recurring alert inside its active date window
- **And** that alert already created one notification-history record earlier on the same day
- **When** a later distinct recurring occurrence triggers another alert notification on that same day
- **Then** the system creates a separate notification-history record for that later occurrence

#### Scenario: Catch-up processing creates notification history for a missed window
- **Given** an authenticated user has an alert that became eligible during a missed evaluation window
- **When** catch-up processing reaches that missed window
- **Then** the system creates the corresponding notification-history record without requiring the original window to be rerun manually
