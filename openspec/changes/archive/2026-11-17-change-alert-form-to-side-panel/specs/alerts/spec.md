## REMOVED Requirements

### Requirement: Guide Alert Creation Through Visible Steps
**Reason**: Alert creation and editing move into a single side panel instead of a multi-step flow.
**Migration**: Covered by the `Author Alerts In A Side Panel Over The Alerts List` requirement.

## MODIFIED Requirements

### Requirement: Start Alert Authoring With Coin Selection
The system SHALL begin create and edit alert flows by asking the user to choose the coin that the alert will target from the authenticated user's watchlist, while allowing contextual entry points to preselect that coin without skipping the coin field.

#### Scenario: User creates a new alert from the alerts workspace
- **Given** an authenticated user opens the create-alert panel from the `Alerts` workspace
- **When** the panel opens
- **Then** the system shows the coin field for the user to choose a coin from the user's watchlist
- **And** the system does not automatically preselect a watchlist coin on that direct entry path

#### Scenario: User creates a new alert from a watchlist asset
- **Given** an authenticated user starts alert creation from a saved asset in the `Watchlist` workspace
- **When** the create-alert panel opens
- **Then** the system preselects the saved asset that launched the flow
- **And** the user can still change the coin

#### Scenario: User edits an existing alert
- **Given** an authenticated user has an existing alert
- **When** the user opens the edit panel
- **Then** the system loads the existing alert coin and allows changing it before saving

### Requirement: Guide Users Through Three Clear Alert Scenarios
The system SHALL guide alert authoring through only three user-visible scenarios: `Price above`, `Price below`, and `News`.

#### Scenario: User views the scenario choices
- **Given** an authenticated user is creating or editing an alert
- **When** the alert panel shows scenario choices
- **Then** the system presents only `Price above`, `Price below`, and `News`

#### Scenario: User submits an unsupported scenario definition
- **Given** an authenticated user
- **When** the user submits an alert definition with unsupported scenario data
- **Then** the system rejects the request with a validation error

### Requirement: Collect Recurring Alert Dates Through A Calendar UI
The system SHALL collect recurring alert start and end dates through a calendar-based date selection interface.

#### Scenario: User configures a recurring alert
- **Given** an authenticated user has chosen the daily recurring repeat option
- **When** the repeat selector expands
- **Then** the system shows a calendar-based date picker for start and end dates

#### Scenario: User provides an invalid date range
- **Given** an authenticated user is configuring a recurring alert
- **When** the user provides an end date earlier than the start date
- **Then** the system rejects the input with a frontend-safe validation error

## ADDED Requirements

### Requirement: Author Alerts In A Side Panel Over The Alerts List
The system SHALL open alert creation and editing in a side panel next to the `Alerts` list, SHALL keep the list visible on wide viewports, and SHALL use the same panel layout for creating and editing.

#### Scenario: User starts creating an alert
- **Given** an authenticated user is in the `Alerts` workspace on a wide viewport
- **When** the user chooses `New alert`
- **Then** the system opens the alert panel beside the alert list
- **And** the alert list remains visible

#### Scenario: User edits an existing alert in the panel
- **Given** an authenticated user has an existing alert
- **When** the user chooses to edit it
- **Then** the system opens the same panel populated with that alert's coin, scenario, trigger, and repeat settings

#### Scenario: User closes the panel
- **Given** an authenticated user has the alert panel open
- **When** the user cancels or closes the panel without saving
- **Then** the system closes the panel without creating or changing any alert

#### Scenario: User saves an alert
- **Given** an authenticated user has entered a valid alert definition in the panel
- **When** the user saves
- **Then** the system creates or updates the alert
- **And** the panel closes and the alert list shows the saved alert

#### Scenario: Saving fails
- **Given** an authenticated user submits an alert from the panel
- **When** the request fails
- **Then** the system shows a readable error in the panel
- **And** the user's entered values are kept

### Requirement: Use A Full-Screen Panel On Narrow Viewports
The system SHALL show the alert panel using the full screen on narrow viewports.

#### Scenario: User opens the panel on a narrow viewport
- **Given** an authenticated user is using a narrow viewport
- **When** the user opens the alert panel
- **Then** the system shows the panel across the full screen
- **And** the user can return to the alert list by closing the panel

### Requirement: Show A Single Readable Alert Summary
The system SHALL describe the alert being authored in one readable summary line and SHALL NOT show separate preview or guidance panels.

#### Scenario: User sets a price trigger
- **Given** an authenticated user is creating or editing a price alert
- **When** the user sets or changes the trigger value
- **Then** the system shows one readable line describing when the alert will trigger

#### Scenario: Trigger is not yet set
- **Given** an authenticated user is creating a price alert
- **When** no trigger value has been entered
- **Then** the system shows a prompt to choose a trigger value instead of a trigger description

### Requirement: Fit The Price Chart To The Visible Price Range
The system SHALL scale the price chart's vertical axis to the price range of the displayed data with comfortable padding, so that price movement and the trigger level are readable and can be selected by clicking the chart.

#### Scenario: Chart displays a coin price history
- **Given** an authenticated user is creating or editing a price alert
- **When** the chart renders price data for the selected scope
- **Then** the system scales the vertical axis to the displayed prices rather than starting at zero

#### Scenario: User clicks the chart to set a trigger
- **Given** an authenticated user is creating or editing a price alert
- **When** the user clicks a point on the chart
- **Then** the system sets the trigger value from that price according to the selected `%` or `$` mode

### Requirement: Select Alert Repeat Behavior With A Single Control
The system SHALL let the user choose alert time behavior with a single `Repeat` control offering `Once` and a daily option within a date range, and SHALL default to `Once`.

#### Scenario: User keeps the default repeat behavior
- **Given** an authenticated user is creating an alert
- **When** the user does not change the repeat control
- **Then** the system saves the alert with one-time behavior

#### Scenario: User chooses the daily option
- **Given** an authenticated user is creating or editing an alert
- **When** the user chooses the daily option
- **Then** the system requires a start date and an end date before saving

### Requirement: Show News Alerts Without A Chart Or Trigger Value
The system SHALL NOT show the price chart or a trigger value control when the selected scenario is `News`.

#### Scenario: User chooses News
- **Given** an authenticated user is creating or editing an alert
- **When** the user selects the `News` scenario
- **Then** the system hides the price chart and trigger value control
- **And** the system shows that the alert notifies about any new article for the selected coin

### Requirement: Handle Panel Loading And Error States
The system SHALL show clear loading and error states for the data the alert panel depends on.

#### Scenario: Watchlist or price data is loading
- **Given** an authenticated user opens the alert panel
- **When** the watchlist or price data is still loading
- **Then** the system shows a loading state in the affected area

#### Scenario: Watchlist or price data fails to load
- **Given** an authenticated user opens the alert panel
- **When** loading the watchlist or price data fails
- **Then** the system shows a readable error with a retry action

#### Scenario: Alert being edited is not found
- **Given** an authenticated user opens the edit panel for an alert
- **When** that alert no longer exists
- **Then** the system shows a not-found message with a way back to the alert list
