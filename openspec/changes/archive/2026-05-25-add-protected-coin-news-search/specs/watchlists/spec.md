## MODIFIED Requirements

### Requirement: Keep Selected Asset Context in Sync
The system SHALL maintain one selected saved asset and update all watchlist information cards when that selected asset changes.

#### Scenario: User selects a different saved asset
- **Given** an authenticated user has multiple saved assets in the watchlist
- **When** the user selects a different asset from the saved-assets list
- **Then** the system updates the summary, chart, and related-news cards to match the selected asset
- **And** the related-news card uses the dedicated protected coin-news lookup flow for the active selection

### Requirement: Show Watchlist Context and Empty States
The system SHALL show selected-asset context cards for summary, chart, and related news, and SHALL provide explicit empty states when the watchlist has no saved assets.

#### Scenario: Watchlist has a selected asset
- **Given** an authenticated user has a selected saved asset in the watchlist
- **When** the watchlist workspace renders
- **Then** the system shows summary, chart, and related-news cards for that asset
- **And** the related-news card shows explicit loading, empty, and error states while fetching dedicated coin-news results
- **And** the related-news card shows an article image when one is available and falls back gracefully when it is not
