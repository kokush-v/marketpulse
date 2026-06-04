## MODIFIED Requirements

### Requirement: Support Alert Time Behavior Modes
The system SHALL allow the user to configure time behavior for all alert types, SHALL evaluate all supported alert types through scheduled background processing every five minutes, and SHALL allow eligible alert triggers to produce Telegram notifications when the user has an active Telegram connection.

#### Scenario: User creates a one-time alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the `one-time` behavior
- **Then** the system stores that alert as a one-time alert

#### Scenario: User creates a daily recurring alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the `daily recurring` behavior
- **Then** the system requires a start date and an end date for that alert
- **And** the system stores that alert as a recurring alert with those date boundaries

#### Scenario: Supported alert types are evaluated on schedule
- **Given** an authenticated user has active alerts of type `Price above`, `Price below`, and `News`
- **When** a scheduled five-minute evaluation window runs
- **Then** the system evaluates each eligible alert type according to its configured rule semantics

#### Scenario: Connected user receives Telegram alert delivery
- **Given** an authenticated user has an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger during scheduled evaluation
- **When** the system processes that alert trigger
- **Then** the system may deliver the resulting alert notification to the user's linked Telegram account

#### Scenario: User without Telegram link triggers an alert
- **Given** an authenticated user does not have an active Telegram link
- **And** one of the user's alerts becomes eligible to trigger during scheduled evaluation
- **When** the system processes that alert trigger
- **Then** the system does not require Telegram delivery to treat the alert trigger as valid

### Requirement: Limit Recurring Alerts To One Trigger Per Day
The system SHALL model recurring alerts so they may trigger at most once per calendar day during their configured active date window, including during catch-up processing of missed evaluation windows.

#### Scenario: Recurring alert already triggered today
- **Given** an authenticated user has a daily recurring alert
- **And** that alert has already triggered once on the current day
- **When** future alert evaluation checks run again on that same day
- **Then** the system treats that alert as ineligible until the next day

#### Scenario: Next day begins inside the recurring window
- **Given** an authenticated user has a daily recurring alert
- **And** the alert triggered on a previous day
- **When** the next day begins and the alert is still inside its configured date range
- **Then** the system treats that alert as eligible again for one trigger on that new day

#### Scenario: Catch-up processing spans multiple missed runs in the same day
- **Given** an authenticated user has a daily recurring alert
- **And** multiple five-minute evaluation windows were missed on the same calendar day
- **When** catch-up processing evaluates those missed windows
- **Then** the system does not trigger that recurring alert more than once for that day
