## REMOVED Requirements

### Requirement: Present Alerts As Readable Cards
**Reason**: Replaced by a presentation that supports both a compact list view and a card view.
**Migration**: Covered by the `Present Alerts In Switchable List And Card Views` requirement, which keeps the readable summary, lifecycle actions, and empty state.

## ADDED Requirements

### Requirement: Present Alerts In Switchable List And Card Views
The system SHALL present saved alerts in the `Alerts` workspace in either a compact list view or a card view, SHALL show the list view by default, and SHALL group alerts by coin in both views.

#### Scenario: User has saved alerts
- **Given** an authenticated user has one or more saved alerts
- **When** the `Alerts` workspace renders for the first time
- **Then** the system shows the alerts in the list view grouped by coin
- **And** each alert shows its scenario, a readable rule summary, its timing, and its status

#### Scenario: User switches to the card view
- **Given** an authenticated user is viewing alerts in the list view
- **When** the user switches to the card view
- **Then** the system shows the same alerts as cards grouped by coin
- **And** each card shows the same scenario, rule summary, timing, and status

#### Scenario: User has no saved alerts
- **Given** an authenticated user has no saved alerts
- **When** the user opens the `Alerts` workspace
- **Then** the system shows an empty state that encourages creating the first alert

#### Scenario: Alerts are loading or fail to load
- **Given** an authenticated user opens the `Alerts` workspace
- **When** the alerts are still loading or the request fails
- **Then** the system shows a loading state while loading
- **And** the system shows an error state with a retry action when the request fails

### Requirement: Manage Alert Lifecycle From The List
The system SHALL let the user pause or resume an alert through a direct on/off control and SHALL provide edit and delete actions for each alert in both views.

#### Scenario: User pauses an alert from the list
- **Given** an authenticated user sees an active alert in the `Alerts` workspace
- **When** the user turns that alert's status control off
- **Then** the system pauses the alert
- **And** the alert is shown as paused

#### Scenario: User resumes an alert from the list
- **Given** an authenticated user sees a paused alert in the `Alerts` workspace
- **When** the user turns that alert's status control on
- **Then** the system resumes the alert
- **And** the alert is shown as active

#### Scenario: User opens alert actions
- **Given** an authenticated user sees an alert in the `Alerts` workspace
- **When** the user opens that alert's actions
- **Then** the system offers edit and delete actions

#### Scenario: Pause or resume fails
- **Given** an authenticated user changes an alert's status
- **When** the request fails
- **Then** the system shows a readable error
- **And** the alert keeps showing its previous status

### Requirement: Remember The Preferred Alerts View
The system SHALL remember the user's chosen alerts view between visits in the same browser and SHALL fall back to the list view when no preference can be read.

#### Scenario: User returns after choosing the card view
- **Given** an authenticated user previously chose the card view
- **When** the user opens the `Alerts` workspace again in the same browser
- **Then** the system shows the alerts in the card view

#### Scenario: Preference cannot be read
- **Given** an authenticated user has no stored view preference or browser storage is unavailable
- **When** the user opens the `Alerts` workspace
- **Then** the system shows the alerts in the list view

### Requirement: Filter Alerts By Status, Coin, And Scenario
The system SHALL let the user filter the displayed alerts by status (`All`, `Active`, `Paused`), by coin through a search field matching coin name or symbol, and by scenario type (`Price above`, `Price below`, `News`), and SHALL apply all active filters together.

#### Scenario: User filters by status
- **Given** an authenticated user has both active and paused alerts
- **When** the user selects the `Paused` status filter
- **Then** the system shows only paused alerts
- **And** each status option shows the number of alerts it matches

#### Scenario: User searches by coin
- **Given** an authenticated user has alerts for several coins
- **When** the user enters a coin name or symbol in the search field
- **Then** the system shows only alerts for coins matching that text

#### Scenario: User filters by scenario type
- **Given** an authenticated user has alerts of several scenario types
- **When** the user selects a scenario type filter
- **Then** the system shows only alerts of that scenario type

#### Scenario: User combines filters
- **Given** an authenticated user has applied more than one filter
- **When** the list renders
- **Then** the system shows only alerts that match every applied filter

#### Scenario: No alerts match the filters
- **Given** an authenticated user has saved alerts
- **When** the applied filters match none of them
- **Then** the system shows a no-results state with an action to clear the filters
- **And** the system does not show the first-alert empty state

### Requirement: Show Concise Readable Alert Summaries
The system SHALL show each alert's rule and timing in readable form without repeating the same information within one alert, SHALL format recurring dates in a human-readable way, and SHALL NOT show a meaningless label for scenarios that have no trigger mode.

#### Scenario: Alert summary does not repeat itself
- **Given** an authenticated user has an alert whose subtitle and rule summary express the same condition
- **When** the alert renders in either view
- **Then** the system shows that condition once

#### Scenario: Recurring alert shows readable dates
- **Given** an authenticated user has a daily recurring alert
- **When** the alert renders in either view
- **Then** the system shows its start and end dates in a human-readable format

#### Scenario: News alert has no trigger mode label
- **Given** an authenticated user has a news alert
- **When** the alert renders in either view
- **Then** the system does not show a generic placeholder label for a trigger mode

### Requirement: Confirm Alert Deletion
The system SHALL ask the user to confirm before deleting an alert.

#### Scenario: User confirms deletion
- **Given** an authenticated user chose to delete an alert
- **When** the user confirms in the confirmation dialog
- **Then** the system deletes the alert
- **And** the alert disappears from the list

#### Scenario: User cancels deletion
- **Given** an authenticated user chose to delete an alert
- **When** the user cancels in the confirmation dialog
- **Then** the system keeps the alert unchanged

#### Scenario: Deletion fails
- **Given** an authenticated user confirmed deleting an alert
- **When** the request fails
- **Then** the system shows a readable error
- **And** the alert remains in the list

### Requirement: Filter Alerts On The Backend
The system SHALL perform alert filtering in the backend: the alert list request SHALL accept optional filters for status, scenario type, and coin name or symbol, SHALL return only the authenticated user's alerts that match every provided filter, and SHALL return alert counts per status.

#### Scenario: Request without filters
- **Given** an authenticated user has saved alerts
- **When** the alert list is requested without filters
- **Then** the system returns all of that user's alerts

#### Scenario: Request with filters
- **Given** an authenticated user has alerts of several statuses, scenarios, and coins
- **When** the alert list is requested with a status, a scenario type, and a coin search text
- **Then** the system returns only that user's alerts matching all provided filters
- **And** the coin search matches the coin name or symbol regardless of letter case

#### Scenario: Status counts ignore the selected status
- **Given** an authenticated user requests the alert list with a coin search or scenario filter
- **When** the system builds the response
- **Then** the system returns the number of matching alerts for `all`, `active`, and `paused`
- **And** those counts reflect the coin search and scenario filters but not the selected status

#### Scenario: Filters never expose other users' alerts
- **Given** another user owns alerts that match the requested filters
- **When** an authenticated user requests the alert list with those filters
- **Then** the system does not return the other user's alerts

#### Scenario: Request with an unsupported filter value
- **Given** an authenticated user
- **When** the alert list is requested with an unsupported status or scenario value
- **Then** the system rejects the request with a validation error
