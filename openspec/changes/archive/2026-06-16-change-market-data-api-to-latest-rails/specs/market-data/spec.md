## MODIFIED Requirements

### Requirement: Serve Public Crypto Market Data Through a Dedicated Ruby Service
The system SHALL obtain public crypto market overview data through a dedicated Ruby on Rails service that integrates with CoinGecko on the server side, while exposing the frontend-facing contract through the primary FastAPI backend, and SHALL preserve that contract through approved Ruby or Rails runtime upgrades of the dedicated service.

#### Scenario: Frontend requests public crypto market data after runtime upgrade
- **Given** the dedicated Ruby market-data service has been upgraded to an approved newer Ruby or Rails runtime
- **When** the frontend requests public crypto market data through the FastAPI backend
- **Then** the request is still handled through the FastAPI backend
- **And** the FastAPI backend still retrieves the market overview from the Ruby market-data service
- **And** the frontend does not call CoinGecko or the Ruby service directly

#### Scenario: Production request uses a reusable market overview snapshot after runtime upgrade
- **Given** a production deployment has a successful reusable market overview snapshot available
- **And** the dedicated Ruby market-data service runtime has been upgraded
- **When** the frontend requests public crypto market data through the FastAPI backend
- **Then** the Ruby market-data service SHALL still prefer returning the reusable snapshot instead of rebuilding the full upstream payload during that request

#### Scenario: Provider limit or failure occurs during snapshot refresh after runtime upgrade
- **Given** the upgraded Ruby market-data service depends on CoinGecko provider responses
- **And** the service has a previously successful market overview snapshot
- **When** CoinGecko returns an error, malformed payload, timeout, or rate-limit response during a refresh attempt
- **Then** the Ruby market-data service SHALL keep the last successful snapshot available when policy allows
- **And** the FastAPI backend continues to receive either a safe reusable snapshot response or a frontend-safe upstream failure response
