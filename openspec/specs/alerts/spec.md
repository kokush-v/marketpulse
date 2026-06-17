# alerts Specification

## Purpose
TBD - created by archiving change add-alert-management. Update Purpose after archive.
## Requirements
### Requirement: Provide A Protected Alerts Workspace
The system SHALL provide authenticated users with a protected `Alerts` workspace for managing personal crypto alerts.

#### Scenario: Authenticated user opens the alerts workspace
- **Given** an authenticated user
- **When** the user navigates to the `Alerts` workspace
- **Then** the system shows only that user's saved alerts

#### Scenario: Unauthenticated visitor requests the alerts workspace
- **Given** a visitor without an authenticated session
- **When** the visitor requests the `Alerts` workspace
- **Then** the system requires sign-in before granting access

### Requirement: Allow Users To Manage Personal Alerts
The system SHALL allow an authenticated user to create, list, edit, pause, resume, and delete personal alerts.

#### Scenario: User creates an alert
- **Given** an authenticated user
- **When** the user submits a valid alert definition
- **Then** the system creates a new alert owned by that user

#### Scenario: User edits an alert
- **Given** an authenticated user has an existing alert
- **When** the user submits valid changes to that alert
- **Then** the system updates that alert, including its coin and rule definition when requested

#### Scenario: User pauses an alert
- **Given** an authenticated user has an active alert
- **When** the user chooses to pause the alert
- **Then** the system marks that alert as paused

#### Scenario: User resumes an alert
- **Given** an authenticated user has a paused alert
- **When** the user chooses to resume the alert
- **Then** the system marks that alert as active

#### Scenario: User deletes an alert
- **Given** an authenticated user has an existing alert
- **When** the user chooses to delete the alert
- **Then** the system removes that alert from the user's alert list

### Requirement: Enforce User Ownership For Alerts
The system SHALL scope all alert-management behavior to the authenticated user's own alert records.

#### Scenario: User lists alerts
- **Given** an authenticated user
- **When** the user requests the alert list
- **Then** the system returns only alerts owned by that user

#### Scenario: User accesses another user's alert
- **Given** an authenticated user
- **And** another user owns an alert
- **When** the authenticated user attempts to view, edit, pause, resume, or delete that other user's alert
- **Then** the system rejects the request according to protected resource rules

### Requirement: Support Absolute Price Threshold Conditions
The system SHALL support alert conditions for a selected coin when the market price moves above or below a user-defined absolute currency value.

#### Scenario: User creates a price-above alert by currency amount
- **Given** an authenticated user
- **When** the user creates an alert for a selected coin with a rule that the price rises above a specific currency value
- **Then** the system stores that alert as a valid absolute-threshold condition

#### Scenario: User creates a price-below alert by currency amount
- **Given** an authenticated user
- **When** the user creates an alert for a selected coin with a rule that the price falls below a specific currency value
- **Then** the system stores that alert as a valid absolute-threshold condition

### Requirement: Support Percentage Threshold Conditions From Creation-Time Price
The system SHALL support alert conditions for a selected coin when the market price moves above or below a user-defined percentage relative to the current price at the moment the alert is created or fully edited.

#### Scenario: User creates a percentage-above alert
- **Given** an authenticated user
- **And** the current price for the selected coin is available
- **When** the user creates an alert with a percentage-above threshold
- **Then** the system captures the current price as the baseline for that condition
- **And** the system stores the percentage threshold with that baseline

#### Scenario: User creates a percentage-below alert
- **Given** an authenticated user
- **And** the current price for the selected coin is available
- **When** the user creates an alert with a percentage-below threshold
- **Then** the system captures the current price as the baseline for that condition
- **And** the system stores the percentage threshold with that baseline

#### Scenario: User updates a percentage-based alert
- **Given** an authenticated user has an existing percentage-based alert
- **And** the current price for the selected coin is available
- **When** the user fully updates that alert
- **Then** the system captures a new current-price baseline for the updated percentage-based condition set

### Requirement: Support Coin News Subscription Conditions
The system SHALL support alert conditions that subscribe the user to any newly available news article for a selected coin.

#### Scenario: User creates a coin-news alert
- **Given** an authenticated user
- **When** the user creates an alert for a selected coin with the coin-news subscription condition
- **Then** the system stores that alert as a valid news-subscription condition

### Requirement: Guide Users Through Three Clear Alert Scenarios
The system SHALL guide alert authoring through only three user-visible scenarios: `Price above`, `Price below`, and `News`.

#### Scenario: User opens the scenario step
- **Given** an authenticated user has selected a coin for a new or existing alert
- **When** the alert authoring flow shows scenario choices
- **Then** the system presents only `Price above`, `Price below`, and `News`

#### Scenario: User submits an unsupported scenario definition
- **Given** an authenticated user
- **When** the user submits an alert definition with unsupported scenario data
- **Then** the system rejects the request with a validation error

### Requirement: Present Alerts As Readable Cards
The system SHALL present saved alerts in the `Alerts` workspace as cards with readable rule summaries and lifecycle actions.

#### Scenario: User has saved alerts
- **Given** an authenticated user has one or more saved alerts
- **When** the `Alerts` workspace renders
- **Then** the system shows cards for those alerts
- **And** each card shows the selected coin name, a readable rule summary, and actions for edit, pause or resume, and delete

#### Scenario: User has no saved alerts
- **Given** an authenticated user has no saved alerts
- **When** the user opens the `Alerts` workspace
- **Then** the system shows an empty state that encourages creating the first alert

### Requirement: Start Alert Authoring With Coin Selection
The system SHALL begin create and edit alert flows by asking the user to choose the coin that the alert will target from the authenticated user's watchlist, while allowing contextual entry points to preselect that coin without skipping the selection step.

#### Scenario: User creates a new alert from the alerts workspace
- **Given** an authenticated user opens the create-alert flow from the `Alerts` workspace
- **When** the alert authoring flow begins
- **Then** the system first asks the user to choose the coin for the alert from the user's watchlist
- **And** the system does not automatically preselect a watchlist coin on that direct entry path

#### Scenario: User creates a new alert from a watchlist asset
- **Given** an authenticated user starts alert creation from a saved asset in the `Watchlist` workspace
- **When** the alert authoring flow begins
- **Then** the system opens on the coin-selection step
- **And** the system preselects the saved asset that launched the flow

#### Scenario: User edits an existing alert
- **Given** an authenticated user has an existing alert
- **When** the user opens the edit flow
- **Then** the system loads the existing alert coin and allows changing it before saving

### Requirement: Allow Missing Coins To Be Added To The Watchlist During Alert Creation
The system SHALL allow an authenticated user to add a missing coin to the personal watchlist from the alert authoring flow and continue creating the alert without leaving that flow.

#### Scenario: User needs a coin that is not in the watchlist
- **Given** an authenticated user is creating or editing an alert
- **And** the needed coin is not currently in the user's watchlist
- **When** the user chooses the add-to-watchlist action from the alert flow
- **Then** the system adds that coin to the user's watchlist
- **And** the coin becomes available for selection in the same alert flow

#### Scenario: Watchlist-scoped picker excludes unrelated coins
- **Given** an authenticated user is creating or editing an alert
- **When** the coin-selection step renders
- **Then** the primary coin list contains only coins from that user's watchlist

### Requirement: Use A Chart-First Flow For Price Alerts
The system SHALL use an interactive price chart as the main authoring context when the user creates or edits `Price above` or `Price below` alerts.

#### Scenario: User chooses Price above
- **Given** an authenticated user has selected a coin
- **When** the user chooses the `Price above` scenario
- **Then** the system shows an interactive price chart for that coin as the primary alert-authoring context

#### Scenario: User chooses Price below
- **Given** an authenticated user has selected a coin
- **When** the user chooses the `Price below` scenario
- **Then** the system shows an interactive price chart for that coin as the primary alert-authoring context

### Requirement: Guide Alert Creation Through Visible Steps
The system SHALL use a visible stepper to guide the user through alert creation and editing.

#### Scenario: User moves through alert creation
- **Given** an authenticated user is creating or editing an alert
- **When** the flow renders
- **Then** the system shows the current step and the remaining steps
- **And** the user advances through the flow in a clear sequence instead of facing one large undifferentiated form

### Requirement: Provide A Single Trigger Control With Percent Or Currency Mode
The system SHALL provide one trigger-value control for price alerts and SHALL allow the user to switch that control between percentage mode and currency-value mode through a `% / $` toggle.

#### Scenario: User creates a price alert in currency mode
- **Given** an authenticated user has selected `Price above` or `Price below`
- **When** the user sets the trigger control to `$`
- **Then** the system accepts an absolute currency trigger value for that alert

#### Scenario: User creates a price alert in percentage mode
- **Given** an authenticated user has selected `Price above` or `Price below`
- **When** the user sets the trigger control to `%`
- **Then** the system accepts a percentage trigger value relative to the current price at creation or full edit time

### Requirement: Support Price-Chart Scope Switching
The system SHALL allow the user to switch the price chart between `1D`, `1W`, and `1M` scopes while creating or editing price alerts.

#### Scenario: User changes chart scope
- **Given** an authenticated user is creating or editing a `Price above` or `Price below` alert
- **When** the user switches the chart scope to `1D`, `1W`, or `1M`
- **Then** the system updates the displayed chart to that selected time scope

### Requirement: Show The Trigger Value On The Chart
The system SHALL render the configured trigger value directly on the chart while the user creates or edits a price alert.

#### Scenario: User sets a price trigger
- **Given** an authenticated user is creating or editing a `Price above` or `Price below` alert
- **When** the user enters or changes the trigger value
- **Then** the system displays that trigger on the chart in the active time scope

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

#### Scenario: User creates a daily recurring alert
- **Given** an authenticated user is creating any supported alert type
- **When** the user chooses the `daily recurring` behavior
- **Then** the system requires a start date and an end date for that alert
- **And** the system stores that alert as a daily recurring alert with those date boundaries

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

### Requirement: Allow Multiple Recurring Triggers Per Day When State Advances
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

### Requirement: Collect Recurring Alert Dates Through A Calendar UI
The system SHALL collect recurring alert start and end dates through a calendar-based date selection interface.

#### Scenario: User configures a recurring alert
- **Given** an authenticated user has selected `daily recurring` behavior
- **When** the time-behavior step renders
- **Then** the system shows a calendar-based date picker for start and end dates

#### Scenario: User provides an invalid date range
- **Given** an authenticated user is configuring a recurring alert
- **When** the user provides an end date earlier than the start date
- **Then** the system rejects the input with a frontend-safe validation error

### Requirement: Return Frontend-Safe Validation And Access Errors
The system SHALL return frontend-safe errors for invalid alert definitions, unavailable baseline price lookups, and unauthorized resource access.

#### Scenario: Selected coin price cannot be resolved for a percentage rule
- **Given** an authenticated user is creating or editing a percentage-based alert
- **When** the system cannot resolve the current price needed for the baseline
- **Then** the system rejects the request with a frontend-safe error

#### Scenario: User submits an invalid threshold value
- **Given** an authenticated user
- **When** the user submits an alert with an invalid threshold value
- **Then** the system rejects the request with a validation error suitable for frontend display
