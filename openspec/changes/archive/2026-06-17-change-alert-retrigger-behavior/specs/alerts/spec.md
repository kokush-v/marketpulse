## MODIFIED Requirements

### Requirement: Support Alert Time Behavior Modes
The system SHALL allow the user to configure time behavior for all alert types, SHALL evaluate all supported alert types through scheduled background processing every five minutes, SHALL allow eligible alert triggers to produce Telegram notifications when the user has an active Telegram connection, and SHALL centralize shared alert-trigger orchestration while creating scenario-specific evaluators through a common creator flow.

#### Scenario: User creates a one-time alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the `one-time` behavior
- **Then** the system stores that alert as a one-time alert

#### Scenario: One-time alert auto-pauses after a successful trigger
- **Given** an authenticated user has an active one-time alert
- **And** that alert successfully triggers during scheduled evaluation
- **When** the system records the trigger outcome
- **Then** the system transitions that alert into a paused state
- **And** the protected product surfaces show that alert as paused

#### Scenario: User resumes a previously triggered one-time price alert
- **Given** an authenticated user has a paused one-time price alert that previously triggered
- **When** the user resumes that alert
- **Then** the system re-arms the alert from the current market state at resume time
- **And** the alert does not continue using the stale baseline from before the pause

#### Scenario: User resumes a previously triggered one-time news alert
- **Given** an authenticated user has a paused one-time news alert that previously triggered
- **When** the user resumes that alert
- **Then** the system re-arms the alert from the current news state at resume time
- **And** the alert does not re-trigger on articles that were already visible before the resume action

#### Scenario: User creates a recurring alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the recurring behavior
- **Then** the system requires a start date and an end date for that alert
- **And** the system stores that alert as a recurring alert with those date boundaries

#### Scenario: Supported alert types are evaluated on schedule
- **Given** an authenticated user has active alerts of type `Price above`, `Price below`, and `News`
- **When** a scheduled five-minute evaluation window runs
- **Then** the system evaluates each eligible alert type according to its configured rule semantics

#### Scenario: Shared orchestration creates scenario-specific evaluators
- **Given** scheduled alert evaluation needs to process eligible alerts for one alert family
- **When** the backend enters the family-specific evaluation flow
- **Then** the system uses shared orchestration for dispatch and persistence behavior
- **And** the system creates the scenario-specific evaluator through a creator-defined factory method rather than branching all evaluation logic inside one shared evaluator implementation

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
The system SHALL keep recurring alerts eligible throughout their configured active date window and SHALL allow multiple legitimate trigger occurrences on the same calendar day when each later occurrence is based on newly advanced alert state rather than the prior stale state.

#### Scenario: Recurring price alert triggers again after a successful re-arm
- **Given** an authenticated user has a recurring percentage-based price alert inside its active date window
- **And** that alert successfully triggered earlier on the same day
- **When** the market later moves enough from the newly re-armed baseline to satisfy the alert condition again
- **Then** the system treats the alert as eligible for another trigger on that same day

#### Scenario: Recurring price alert updates its baseline after trigger
- **Given** an authenticated user has a recurring percentage-based price alert inside its active date window
- **When** that alert successfully triggers
- **Then** the system updates the alert's active baseline to the current price state used for the successful trigger
- **And** later evaluations compare against that newer baseline

#### Scenario: Recurring news alert notifies on multiple new articles in one day
- **Given** an authenticated user has a recurring news alert inside its active date window
- **And** one new article already triggered a notification earlier on the same day
- **When** a different newer article becomes available later that same day
- **Then** the system treats the alert as eligible for another trigger for that later article

#### Scenario: Recurring alert outside its date window stays ineligible
- **Given** an authenticated user has a recurring alert
- **When** scheduled evaluation runs outside the alert's configured start and end dates
- **Then** the system does not trigger that recurring alert
