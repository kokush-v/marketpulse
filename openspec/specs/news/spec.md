# news Specification

## Purpose
Define the protected coin-news lookup contract and its watchlist-facing usage for authenticated users.

## Requirements
### Requirement: Provide Protected Coin News Search
The system SHALL provide a protected `GET /news` endpoint that allows an authenticated user to request the latest news for a cryptocurrency query.

#### Scenario: Authenticated user requests coin news
- **Given** an authenticated user
- **When** the user requests `GET /news` with a valid `query` value
- **Then** the system returns a news-search response for that coin query

### Requirement: Serve Coin News Through The Market-Data Microservice
The system SHALL serve authenticated coin-news lookups through the `market-data` microservice rather than calling the external news provider directly from frontend clients.

#### Scenario: Frontend requests coin news
- **Given** an authenticated user requests `GET /news` with a valid `query` value
- **When** the primary backend handles the request
- **Then** the primary backend retrieves coin-news results through the `market-data` microservice
- **And** the frontend does not call NewsAPI or the `market-data` microservice directly

#### Scenario: Unauthenticated visitor requests coin news
- **Given** a visitor without an authenticated session
- **When** the visitor requests `GET /news`
- **Then** the system rejects the request according to protected endpoint rules

### Requirement: Accept Coin Name Or Symbol Input
The system SHALL accept a required `query` parameter whose value represents a cryptocurrency coin name or symbol.

#### Scenario: User searches by coin name
- **Given** an authenticated user
- **When** the user requests `GET /news?query=bitcoin`
- **Then** the system performs a coin-news lookup for that coin name

#### Scenario: User searches by symbol
- **Given** an authenticated user
- **When** the user requests `GET /news?query=BTC`
- **Then** the system performs a coin-news lookup for that symbol

#### Scenario: User omits the query parameter
- **Given** an authenticated user
- **When** the user requests `GET /news` without a valid `query` value
- **Then** the system returns a validation error instead of performing a provider lookup

### Requirement: Return Latest Available Articles Without Persistence
The system SHALL fetch latest available coin-news results on demand through the `market-data` microservice provider integration and SHALL NOT persist those articles as part of this capability.

#### Scenario: Matching articles are available
- **Given** an authenticated user requests coin news with a valid `query`
- **When** the provider returns matching articles
- **Then** the system returns a normalized list of latest available articles
- **And** the system does not require previously stored article records to fulfill the request

#### Scenario: Matching article includes an image
- **Given** an authenticated user requests coin news with a valid `query`
- **And** the provider returns an article with an image URL
- **When** the system normalizes the response
- **Then** the returned article includes that image URL in an optional field

#### Scenario: Matching article has no image
- **Given** an authenticated user requests coin news with a valid `query`
- **And** the provider returns an article without an image URL
- **When** the system normalizes the response
- **Then** the returned article remains valid without requiring an image field

#### Scenario: No matching articles are available
- **Given** an authenticated user requests coin news with a valid `query`
- **When** the provider returns no matching articles
- **Then** the system returns a successful empty result set

### Requirement: Feed The Watchlist Related Updates Card
The system SHALL allow the protected watchlist workspace to use the `/news` endpoint as the source for the existing `Related updates` card of the selected asset.

#### Scenario: Selected watchlist asset updates the news card
- **Given** an authenticated user has a selected saved asset in the watchlist
- **When** the watchlist workspace requests related updates for that selected asset
- **Then** the system uses the protected `/news` endpoint to retrieve the latest related articles
- **And** the existing `Related updates` card refreshes to match the selected asset

### Requirement: Degrade Gracefully On Provider Failure
The system SHALL map upstream provider failures into safe backend-defined error behavior for clients.

#### Scenario: Provider rate limit or upstream error occurs
- **Given** an authenticated user requests coin news with a valid `query`
- **When** the news provider returns an error, malformed payload, or rate-limit response
- **Then** the system returns a frontend-safe error response
- **And** the response does not expose provider credentials or raw provider internals
