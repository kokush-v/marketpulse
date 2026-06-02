## MODIFIED Requirements

### Requirement: Support Alert Time Behavior Modes
The system SHALL allow the user to configure time behavior for all alert types and SHALL allow eligible alert triggers to produce Telegram notifications when the user has an active Telegram connection.

#### Scenario: User creates a one-time alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the `one-time` behavior
- **Then** the system stores that alert as a one-time alert

#### Scenario: User creates a daily recurring alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the `daily recurring` behavior
- **Then** the system requires a start date and an end date for that alert
- **And** the system stores that alert as a recurring alert with those date boundaries

#### Scenario: Connected user receives Telegram alert delivery
- **Given** an authenticated user has an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger
- **When** the system processes that alert trigger
- **Then** the system may deliver the resulting alert notification to the user's linked Telegram account

#### Scenario: User without Telegram link triggers an alert
- **Given** an authenticated user does not have an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger
- **When** the system processes that alert trigger
- **Then** the system does not require Telegram delivery to treat the alert trigger as valid
