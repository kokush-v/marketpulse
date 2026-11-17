## ADDED Requirements

### Requirement: Present A Consistent MarketPulse Brand Mark
The system SHALL present one custom MarketPulse brand mark in the dashboard sidebar header, on the authentication pages, and as the browser tab icon, and SHALL NOT use the same icon for the brand and for a navigation item.

#### Scenario: User views the dashboard sidebar
- **Given** a user opens the dashboard shell
- **When** the sidebar header renders
- **Then** the system shows the MarketPulse brand mark next to the `MarketPulse` name

#### Scenario: Sidebar is collapsed
- **Given** a user has collapsed the sidebar to icons
- **When** the sidebar header renders
- **Then** the system still shows the MarketPulse brand mark, fully visible

#### Scenario: User opens an authentication page
- **Given** a user opens the sign in, sign up, reset password, or update password page
- **When** the page renders
- **Then** the system shows the MarketPulse brand mark above the `MarketPulse` name

#### Scenario: User views the browser tab
- **Given** a user opens any page of the application
- **When** the browser shows the tab
- **Then** the system provides the MarketPulse brand mark as the tab icon

#### Scenario: Brand and navigation are distinct
- **Given** a user views the sidebar
- **When** the brand mark and the `Overview` navigation item are shown
- **Then** the system uses a different icon for the `Overview` item than the brand mark

#### Scenario: Mark is shown at small sizes
- **Given** the brand mark is rendered at 16px
- **When** a user views it
- **Then** the rising line and the end point remain distinguishable

### Requirement: Distinguish Sidebar Navigation Items By Icon Color
The system SHALL show each sidebar navigation item with its own icon color, and SHALL keep the item label and active state unchanged.

#### Scenario: User views the sidebar navigation
- **Given** a user opens the dashboard shell
- **When** the sidebar navigation renders
- **Then** the system shows `Overview`, `Watchlist`, `Alerts`, and `Assistant` each with an icon in a different color

#### Scenario: Sidebar is collapsed
- **Given** a user has collapsed the sidebar to icons
- **When** the navigation renders
- **Then** the system keeps the per-item icon colors visible
