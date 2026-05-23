# watchlists Specification

## Purpose
Define the protected personal watchlist experience for authenticated users, including saving starred crypto assets, preventing duplicates, restoring the selected asset, and showing selected-asset summary, chart, and related news context.
## Requirements
### Requirement: Provide a Protected Single Watchlist Workspace
The system SHALL provide authenticated users with a protected `Watchlist` workspace that represents one personal list of starred crypto assets.

#### Scenario: Authenticated user opens the watchlist workspace
- **Given** an authenticated user
- **When** the user navigates to the `Watchlist` workspace
- **Then** the system shows the user's saved starred assets without exposing other users' watchlist data

#### Scenario: Unauthenticated visitor requests the watchlist workspace
- **Given** a visitor without an authenticated session
- **When** the visitor requests the `Watchlist` workspace
- **Then** the system requires sign-in before granting access

### Requirement: Allow Users to Add and Remove Starred Assets
The system SHALL allow an authenticated user to add a crypto asset into the personal watchlist from search results and remove a saved asset from the watchlist later.

#### Scenario: User adds an asset from search results
- **Given** an authenticated user with access to the `Watchlist` workspace
- **And** the user can see search results for crypto assets
- **When** the user uses the star action for a search result
- **Then** the system adds that asset to the user's watchlist

#### Scenario: User removes an asset from the watchlist
- **Given** an authenticated user with a saved asset in the watchlist
- **When** the user chooses `Delete` from that asset's overflow actions
- **Then** the system removes the asset from the user's watchlist

### Requirement: Prevent Duplicate Starred Assets
The system SHALL prevent the same crypto asset from appearing more than once in a user's watchlist.

#### Scenario: User tries to add an already saved asset
- **Given** an authenticated user already has a crypto asset in the watchlist
- **When** the user attempts to star the same asset again
- **Then** the system does not create a duplicate watchlist entry
- **And** the system returns a stable user-visible outcome indicating the asset is already saved

### Requirement: Keep Selected Asset Context in Sync
The system SHALL maintain one selected saved asset and update all watchlist information cards when that selected asset changes.

#### Scenario: User selects a different saved asset
- **Given** an authenticated user has multiple saved assets in the watchlist
- **When** the user selects a different asset from the saved-assets list
- **Then** the system updates the summary, chart, and related-news cards to match the selected asset

#### Scenario: User opens a non-empty watchlist without a valid restored selection
- **Given** an authenticated user has one or more saved assets in the watchlist
- **And** there is no valid previously restored selected asset
- **When** the watchlist workspace loads
- **Then** the system automatically selects the first available saved asset

### Requirement: Preserve Selected Asset Across Page Reloads
The system SHALL preserve the selected saved asset across page reloads by restoring it from browser storage when it is still valid.

#### Scenario: Reload restores a valid selected asset
- **Given** an authenticated user previously selected a saved asset in the watchlist
- **And** that saved asset is still present in the user's watchlist
- **When** the user reloads the page
- **Then** the system restores that asset as the selected asset

#### Scenario: Reload falls back when restored asset is no longer saved
- **Given** browser storage references a previously selected asset
- **And** that asset is no longer present in the user's watchlist
- **When** the watchlist workspace loads
- **Then** the system ignores the stale stored selection
- **And** the system selects the first available saved asset or shows an empty state if no saved assets remain

### Requirement: Show Watchlist Context and Empty States
The system SHALL show selected-asset context cards for summary, chart, and related news, and SHALL provide explicit empty states when the watchlist has no saved assets.

#### Scenario: Watchlist has a selected asset
- **Given** an authenticated user has a selected saved asset in the watchlist
- **When** the watchlist workspace renders
- **Then** the system shows summary, chart, and related-news cards for that asset

#### Scenario: Watchlist is empty
- **Given** an authenticated user has no saved assets in the watchlist
- **When** the user opens the `Watchlist` workspace
- **Then** the system shows an empty state that encourages adding the first saved asset
- **And** the empty state does not present stale selected-asset content

### Requirement: Expose Per-Asset Overflow Actions
The system SHALL expose per-asset overflow actions for delete and future alert entry points without requiring alert creation behavior in this change.

#### Scenario: User opens an asset action menu
- **Given** an authenticated user has a saved asset in the watchlist
- **When** the user opens that asset's overflow actions
- **Then** the system shows at least `Delete` and `Add alert` actions

#### Scenario: User chooses Add alert
- **Given** an authenticated user opens the overflow actions for a saved asset
- **When** the user chooses `Add alert`
- **Then** the system does not create or persist an alert as part of this change
