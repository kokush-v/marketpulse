## MODIFIED Requirements

### Requirement: Serve Coin News Through The Market-Data Microservice
The system SHALL serve authenticated coin-news lookups through the `market-data` microservice rather than calling the external news provider directly from frontend clients, and SHALL preserve that integration contract through approved Ruby or Rails runtime upgrades of the microservice.

#### Scenario: Frontend requests coin news after runtime upgrade
- **Given** an authenticated user requests `GET /news` with a valid `query` value
- **And** the Ruby `market-data` microservice runtime has been upgraded
- **When** the primary backend handles the request
- **Then** the primary backend still retrieves coin-news results through the `market-data` microservice
- **And** the frontend does not call NewsAPI or the `market-data` microservice directly

#### Scenario: Provider failure remains safe after runtime upgrade
- **Given** an authenticated user requests coin news with a valid `query`
- **And** the Ruby `market-data` microservice runtime has been upgraded
- **When** the news provider returns an error, malformed payload, or rate-limit response
- **Then** the system still returns a frontend-safe error response
- **And** the response does not expose provider credentials or raw provider internals
