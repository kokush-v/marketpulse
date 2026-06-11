## MODIFIED Requirements

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
