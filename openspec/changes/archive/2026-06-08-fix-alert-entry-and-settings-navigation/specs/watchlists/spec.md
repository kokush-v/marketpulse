## ADDED Requirements

### Requirement: Keep The Saved-Coins Panel Scrollable
The system SHALL keep the `Your saved coins` panel usable when a user has more saved assets than fit in the available watchlist panel height.

#### Scenario: Watchlist contains many saved assets
- **Given** an authenticated user has enough saved assets to exceed the visible height of the saved-coins panel
- **When** the `Watchlist` workspace renders
- **Then** the system keeps the saved-coins panel within the workspace layout
- **And** the user can scroll inside that panel to reach all saved assets

## MODIFIED Requirements

### Requirement: Expose Per-Asset Overflow Actions
The system SHALL expose per-asset overflow actions for delete and alert entry so a saved asset can launch contextual alert creation without creating the alert immediately.

#### Scenario: User opens an asset action menu
- **Given** an authenticated user has a saved asset in the watchlist
- **When** the user opens that asset's overflow actions
- **Then** the system shows at least `Delete` and `Add alert` actions

#### Scenario: User chooses Add alert
- **Given** an authenticated user opens the overflow actions for a saved asset
- **When** the user chooses `Add alert`
- **Then** the system navigates the user to the create-alert flow
- **And** the system carries that saved asset into the alert coin-selection step as the preselected coin
- **And** the system does not create or persist an alert until the user completes the alert flow
