## ADDED Requirements

### Requirement: Calculate Market Figures With Deterministic Tools

The system SHALL compute coin-to-USD and USD-to-coin conversions, percentage price changes over `24h`, `7d`, `30d`, or `1y`, and the distance between the current price and a target price using deterministic backend tools rather than the language model. Each result SHALL include the inputs used, including the USD rate or prices and their update times. All calculations SHALL use USD.

#### Scenario: User converts a coin amount to USD

- **Given** an authenticated user asks how many dollars 0.5 BTC is worth
- **When** the assistant responds
- **Then** the conversion is calculated by the backend tool
- **And** the response states the USD amount, the BTC rate used, and its update time

#### Scenario: User converts USD to a coin amount

- **Given** an authenticated user asks how much ETH 1000 USD buys
- **When** the assistant responds
- **Then** the response states the calculated ETH amount and the ETH rate used

#### Scenario: User asks for a percentage change over a period

- **Given** an authenticated user asks how much ETH changed over the last week
- **When** the assistant responds
- **Then** the response states the calculated percentage and USD change with the start and end prices for the `7d` period

#### Scenario: User asks for distance to a target price

- **Given** an authenticated user asks how much BTC must rise to reach 120000 USD
- **When** the assistant responds
- **Then** the response states the current price, the USD difference, and the percentage difference calculated by the backend tool

#### Scenario: Calculation uses stale market data

- **Given** the market data used for a calculation is older than the freshness threshold
- **When** the assistant responds with the result
- **Then** it warns that the data may be outdated
- **And** the calculation source is marked as stale

### Requirement: Calculate Distance To An Owned Price Alert

The system SHALL calculate the distance from the current price to the target of one of the authenticated user's active price alerts. For fixed-price alerts the target SHALL be the alert threshold; for percent alerts the target SHALL be derived from the alert's baseline price and threshold percentage. When several active price alerts match the user's request, the assistant SHALL list them and ask the user to choose before calculating. Alerts owned by other users SHALL NOT be used.

#### Scenario: One matching alert

- **Given** an authenticated user has one active price alert for BTC above 100000 USD
- **When** the user asks how far BTC is from their alert
- **Then** the response states the current price, the alert target, and the USD and percentage distance

#### Scenario: Percent alert

- **Given** an authenticated user has an active alert for ETH rising 5% from a baseline price of 3000 USD
- **When** the user asks how far ETH is from that alert
- **Then** the distance is calculated to a target of 3150 USD

#### Scenario: Several matching alerts

- **Given** an authenticated user has three active price alerts for BTC
- **When** the user asks how far BTC is from their alert
- **Then** the assistant lists the three alerts and asks which one to use
- **And** no distance is calculated until the user chooses

#### Scenario: No active price alert matches

- **Given** an authenticated user has only a news alert for BTC
- **When** the user asks how far BTC is from their alert
- **Then** the assistant says there is no active price alert for BTC
- **And** no distance is calculated

### Requirement: Clarify Missing Calculation Inputs

The assistant SHALL ask a clarification question instead of guessing when a calculation request lacks or has ambiguous required inputs, such as the coin, the amount, the period, or the target.

#### Scenario: Amount is missing

- **Given** an authenticated user asks how many dollars their BTC is worth without giving an amount
- **When** the assistant responds
- **Then** it asks for the BTC amount
- **And** no conversion result is given

#### Scenario: Coin is ambiguous

- **Given** an authenticated user asks for a conversion using a coin name that matches several assets
- **When** the assistant responds
- **Then** it lists the matching coins and asks which one is meant

### Requirement: Decline Unsupported Calculations

The assistant SHALL NOT perform market calculations itself. When a user asks for a calculation that no calculation tool supports, the assistant SHALL say that it cannot calculate it.

#### Scenario: User asks for a historical profit calculation

- **Given** an authenticated user asks how much they would have earned by buying 1 BTC a year ago
- **When** the assistant responds
- **Then** it says that it cannot calculate that
- **And** it does not provide a figure

#### Scenario: User asks for a non-USD conversion

- **Given** an authenticated user asks how many euros 1 BTC is worth
- **When** the assistant responds
- **Then** it says that only USD calculations are supported
