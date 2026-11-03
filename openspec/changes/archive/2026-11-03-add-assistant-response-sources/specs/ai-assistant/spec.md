## ADDED Requirements

### Requirement: Show Response Sources Under Assistant Messages

The system SHALL attach to each assistant message the sources of the data returned by the tools used for that response and SHALL display them in a sources block under the message in the assistant widget and page. News sources SHALL include the publisher, article title, publication time, and article link. Price, market, watchlist, and alert data sources SHALL be labeled `MarketPulse knowledge`, SHALL include the data update time when applicable, and SHALL NOT include a link. Sources SHALL be persisted with the message.

#### Scenario: User asks for coin news

- **Given** an authenticated user asks the assistant for the latest news about a coin
- **When** the assistant responds using returned news articles
- **Then** the sources block lists each used article with its publisher, title, publication time, and a link to the article

#### Scenario: User asks for a coin price

- **Given** an authenticated user asks for the current price of a coin
- **When** the assistant responds using market data
- **Then** the sources block shows `MarketPulse knowledge` with the market data update time
- **And** the source has no link

#### Scenario: User asks about personal alerts

- **Given** an authenticated user asks the assistant to list their alerts
- **When** the assistant responds using the user's alert data
- **Then** the sources block shows `MarketPulse knowledge` without a link

#### Scenario: Response uses no data

- **Given** the assistant responds without using any data tool
- **When** the message is displayed
- **Then** no sources block is shown

#### Scenario: User reopens a conversation

- **Given** an assistant message was recorded with sources
- **When** the owning user reopens the conversation
- **Then** the message displays the same sources

### Requirement: Warn About Stale Market Data

The system SHALL treat market data as stale when its update time is older than a configurable freshness threshold, defaulting to 15 minutes, or when its update time is unknown. When an answer uses stale market data, the assistant SHALL still answer, SHALL warn the user in the response that the data may be outdated, and the corresponding source SHALL be marked as stale.

#### Scenario: Price data is older than the threshold

- **Given** the latest available BTC price was updated 5 hours ago
- **When** an authenticated user asks for the current BTC price
- **Then** the assistant states the available price
- **And** warns that the data is outdated and the actual price may differ
- **And** the source is marked as stale with its update time

#### Scenario: Price data is fresh

- **Given** the latest available BTC price was updated within the freshness threshold
- **When** an authenticated user asks for the current BTC price
- **Then** the assistant answers without a staleness warning
- **And** the source is not marked as stale

### Requirement: Answer Only From Available Data

The assistant SHALL state facts and figures only from tool results available in the conversation. When the tools return no data, return an error, or the question requires information outside MarketPulse data, the assistant SHALL tell the user that it cannot answer instead of answering from unsupported knowledge. The assistant MAY describe MarketPulse capabilities in product language.

#### Scenario: Question outside MarketPulse data

- **Given** an authenticated user asks a general question that no assistant tool can answer, such as what staking is
- **When** the assistant responds
- **Then** it says that it cannot answer that question
- **And** it does not provide an answer from unsupported knowledge

#### Scenario: Tool returns no data

- **Given** an authenticated user asks for news about a coin
- **When** the news tool returns no articles
- **Then** the assistant says that no news is available
- **And** it does not invent articles or links

#### Scenario: User asks what the assistant can do

- **Given** an authenticated user asks which tasks the assistant can help with
- **When** the assistant responds
- **Then** it describes supported MarketPulse workflows in product language
