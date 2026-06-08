## MODIFIED Requirements

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
