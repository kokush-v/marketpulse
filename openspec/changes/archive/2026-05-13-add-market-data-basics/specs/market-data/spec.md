## ADDED Requirements

### Requirement: Authenticated Market Data Access

The system SHALL allow authenticated users to request basic market data for a ticker symbol through backend API endpoints.

#### Scenario: Authenticated user requests market data

- Given an authenticated user
- When the user requests market data for ticker `aapl`
- Then the backend shall normalize the symbol to `AAPL`
- And the backend shall process the request without requiring a user ownership identifier in the request body
- And the backend response shall identify the symbol as `AAPL`

#### Scenario: Unauthenticated user requests market data

- Given no authenticated user session
- When market data is requested
- Then the backend shall reject the request as unauthorized

### Requirement: Server-Side Provider Integration

The system SHALL call Finnhub only from the backend and SHALL keep Finnhub credentials out of frontend code and API responses.

#### Scenario: Frontend requests a latest quote

- Given an authenticated user on the frontend
- When the user requests the latest quote for a ticker
- Then the frontend shall call the MarketPulse backend
- And the backend shall call Finnhub using server-side credentials
- And the API response shall not include Finnhub API keys, tokens, or secret configuration values

### Requirement: Latest Quote Retrieval

The system SHALL provide latest quote data for a normalized ticker symbol when provider data is available.

#### Scenario: Latest quote is available

- Given Finnhub returns quote data for `AAPL`
- When an authenticated user requests the latest quote for `aapl`
- Then the backend shall return the current price, daily change, daily percent change, open, high, low, previous close, and quote timestamp when those fields are available
- And the returned symbol shall be `AAPL`

#### Scenario: Latest quote is unavailable

- Given Finnhub returns no usable quote data for `UNKNOWN`
- When an authenticated user requests the latest quote for `UNKNOWN`
- Then the backend shall return a controlled not-found or unavailable response
- And the response shall not expose raw provider error payloads or credentials

### Requirement: Daily Historical Chart Data

The system SHALL support daily historical market data for charts when Finnhub provides access to that data.

#### Scenario: Daily historical data is available

- Given Finnhub returns daily candle data for `AAPL`
- When an authenticated user requests historical data for `AAPL`
- Then the backend shall return daily chart points with timestamp, open, high, low, close, and volume values when those fields are available
- And the response shall identify the resolution as daily

#### Scenario: Historical data is unavailable on the current provider plan

- Given Finnhub denies access to historical candle data for the requested ticker or range
- When an authenticated user requests historical data
- Then the backend shall return a controlled chart-unavailable response
- And the frontend shall allow the user to continue viewing latest quote information when quote data is available

### Requirement: No Intraday Market Data

The system SHALL NOT request or expose intraday market data as part of the basic market-data feature.

#### Scenario: User requests chart data

- Given an authenticated user requests chart data
- When the backend builds a provider request
- Then the request shall use daily historical data only
- And the backend shall not request one-minute, five-minute, fifteen-minute, thirty-minute, or hourly intraday resolutions

### Requirement: Stable Data Caching

The system SHALL cache or persist only market data that is expected to remain stable for a long period.

#### Scenario: Stable data is retrieved

- Given the backend retrieves symbol metadata, company metadata, or completed daily historical candles
- When the data is suitable for reuse
- Then the backend may store or cache that data for future requests

#### Scenario: Volatile quote data is retrieved

- Given the backend retrieves latest quote data
- When the quote represents a current market value
- Then the backend shall not treat that quote as long-term stable data
- And the backend shall avoid long-lived persistent caching for that quote

### Requirement: Provider Failure Handling

The system SHALL handle Finnhub failures and free-plan limitations without breaking the entire market-data view.

#### Scenario: Provider rate limit is reached

- Given Finnhub returns a rate-limit response
- When an authenticated user requests market data
- Then the backend shall return a controlled rate-limit or temporarily-unavailable response
- And the response shall not expose raw provider error payloads or credentials

#### Scenario: Historical chart fails but quote succeeds

- Given latest quote data is available
- And historical chart data is unavailable
- When the frontend renders the market-data view
- Then the frontend shall show the quote data
- And the frontend shall show a non-blocking chart-unavailable state

### Requirement: Backend Test Coverage

The system SHALL include backend tests for market-data behavior using mocked provider responses.

#### Scenario: Backend tests run without real Finnhub access

- Given backend tests for market-data behavior
- When the test suite runs
- Then tests shall use mocked Finnhub responses
- And tests shall not require a real Finnhub API key
- And tests shall cover successful responses, symbol normalization, provider failures, unavailable history, and credential non-exposure
