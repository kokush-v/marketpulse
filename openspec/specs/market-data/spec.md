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

#### Scenario: Provider limit or failure occurs
- **Given** the Ruby market-data service depends on CoinGecko provider responses
- **When** CoinGecko returns an error, malformed payload, or rate-limit response
- **Then** the Ruby market-data service returns a safe upstream failure response
- **And** the FastAPI backend maps that upstream failure into a frontend-safe response that allows the dashboard to degrade gracefully

#### Scenario: Successful overview payload is reused within the cache window
- **Given** the Ruby market-data service has successfully assembled a public crypto market overview payload
- **When** another request for the same overview arrives within one hour
- **Then** the Ruby market-data service MAY serve the cached overview payload instead of calling CoinGecko again

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
