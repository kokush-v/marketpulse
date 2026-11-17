# market-data Specification

## Purpose
Define the public crypto market dashboard contract, including the dashboard shell, the market overview experience, and the backend-served market-data flow that powers it.
## Requirements
### Requirement: Provide a Public Dashboard Shell for Crypto Market Data
The system SHALL provide a public dashboard shell with navigation, header, and content regions that establishes the layout pattern for current and future crypto dashboard tabs.

#### Scenario: Visitor opens the public dashboard
- **Given** a visitor opens the dashboard route without an authenticated session
- **When** the dashboard loads
- **Then** the system shows the dashboard shell without requiring sign-in

#### Scenario: Dashboard shell hosts the default tab
- **Given** the public dashboard shell is available
- **When** a visitor lands on the dashboard
- **Then** the `Market Overview` tab is shown as the default content view

### Requirement: Show a Public Crypto Market Overview Tab
The system SHALL provide a public `Market Overview` tab that presents general crypto-market information in a visually scannable dashboard format.

#### Scenario: Crypto market overview data loads successfully
- **Given** the dashboard is available
- **When** crypto market overview data is successfully returned
- **Then** the page shows asset price, 24-hour change, market cap, volume, chart, coin information, and top gainers/losers modules
- **And** the page may show top assets by market capitalization as part of the same overview
- **And** the first version may limit the public overview universe to a fixed provider-friendly subset to stay within external free-tier constraints

#### Scenario: Crypto market overview data is temporarily unavailable
- **Given** the dashboard is available
- **When** one or more public market-data modules cannot be loaded
- **Then** the page shows a non-blocking loading, empty, or error state for the affected modules

### Requirement: Serve Public Crypto Market Data Through a Dedicated Ruby Service
The system SHALL obtain public crypto market overview data through a dedicated Ruby on Rails service that integrates with CoinGecko on the server side, while exposing the frontend-facing contract through the primary FastAPI backend.

#### Scenario: Frontend requests public crypto market data
- **Given** the public dashboard needs crypto market overview data
- **When** the frontend requests that data
- **Then** the request is handled through the FastAPI backend
- **And** the FastAPI backend retrieves the market overview from the Ruby market-data service
- **And** the frontend does not call CoinGecko or the Ruby service directly

#### Scenario: Production request uses a reusable market overview snapshot
- **Given** a production deployment has a successful reusable market overview snapshot available
- **When** the frontend requests public crypto market data through the FastAPI backend
- **Then** the Ruby market-data service SHALL prefer returning the reusable snapshot instead of rebuilding the full upstream payload during that request
- **And** the service SHALL treat that snapshot as fresh for no longer than fifteen minutes after the most recent successful snapshot refresh

#### Scenario: Provider limit or failure occurs during snapshot refresh
- **Given** the Ruby market-data service depends on CoinGecko provider responses
- **And** the service has a previously successful market overview snapshot
- **When** CoinGecko returns an error, malformed payload, timeout, or rate-limit response during a refresh attempt
- **Then** the Ruby market-data service SHALL keep the last successful snapshot available when policy allows
- **And** that stale fallback window SHALL expire within thirty minutes of the most recent successful snapshot
- **And** the FastAPI backend continues to receive either a safe reusable snapshot response or a frontend-safe upstream failure response

#### Scenario: No successful snapshot exists during a cold start
- **Given** a production deployment does not yet have a successful market overview snapshot
- **When** the first public market overview request arrives
- **Then** the Ruby market-data service MAY perform a bounded initial build attempt
- **And** if the initial build cannot complete within documented limits, the service SHALL return a safe upstream failure response

### Requirement: Keep the Dashboard Public While Supporting Optional Watchlist Context
The system SHALL keep the market dashboard publicly accessible while allowing optional watchlist-related content for authenticated users when such data is available.

#### Scenario: Unauthenticated visitor views the watchlist area
- **Given** a visitor is not authenticated
- **When** the dashboard renders a watchlist area
- **Then** the system shows a non-blocking empty or sign-in state and keeps the rest of the dashboard accessible

#### Scenario: Authenticated user has watchlist data
- **Given** an authenticated user has watchlist data available
- **When** the user opens the public dashboard
- **Then** the dashboard MAY show watchlist-related content as an additive module without requiring a separate protected route
- **And** any watchlist-related asset terminology shall align with crypto assets rather than stocks

### Requirement: Serve Historical Price Series For Assistant Charts

The system SHALL retrieve historical cryptocurrency price series through the backend-owned market-data flow for use in authenticated assistant chart requests. The browser SHALL not call CoinGecko or the Ruby market-data service directly.

#### Scenario: Assistant requests a supported historical series

- **Given** an authenticated assistant chart request identifies one or more supported coins and a supported period
- **When** the primary backend requests their historical price data
- **Then** the Ruby market-data service obtains and normalizes the provider data
- **And** the primary backend receives a safe normalized series response

#### Scenario: Historical-price provider is unavailable

- **Given** an authenticated assistant chart request requires historical provider data
- **When** the provider times out, is rate-limited, or returns malformed data
- **Then** the backend returns a safe recoverable assistant error
- **And** it does not expose provider credentials or raw provider internals

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

