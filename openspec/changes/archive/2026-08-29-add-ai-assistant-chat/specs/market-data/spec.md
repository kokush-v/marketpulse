## ADDED Requirements

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
