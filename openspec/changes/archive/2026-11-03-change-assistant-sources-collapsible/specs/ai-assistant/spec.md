## MODIFIED Requirements

### Requirement: Show Response Sources Under Assistant Messages

The system SHALL attach to each assistant message the sources of the data returned by the tools used for that response and SHALL display them in a sources block under the message in the assistant widget and page. The sources block SHALL be collapsed by default for any number of sources. The collapsed block SHALL show the `Sources` heading, the unique source labels, and the total number of sources, and SHALL let the user expand it. The expanded block SHALL list every source and SHALL let the user collapse it again. In the expanded list, news sources SHALL include the publisher, article title, publication time, and article link. Price, market, watchlist, and alert data sources SHALL be labeled `MarketPulse knowledge`, SHALL include the data update time when applicable, and SHALL NOT include a link. Stale markers SHALL be shown in the expanded list only. Sources SHALL be persisted with the message.

#### Scenario: User asks for coin news

- **Given** an authenticated user asks the assistant for the latest news about a coin
- **When** the assistant responds using returned news articles
- **Then** the collapsed sources block shows the unique publishers and the number of sources
- **And** after the user expands it, the block lists each used article with its publisher, title, publication time, and a link to the article

#### Scenario: User collapses the sources list

- **Given** the sources block of an assistant message is expanded
- **When** the user collapses it
- **Then** the block again shows only the heading, unique source labels, and the number of sources

#### Scenario: User asks for a coin price

- **Given** an authenticated user asks for the current price of a coin
- **When** the assistant responds using market data
- **Then** the collapsed sources block shows `MarketPulse knowledge` and a count of one
- **And** after the user expands it, the source shows the market data update time and has no link

#### Scenario: Stale source in a collapsed block

- **Given** an assistant message has a source marked as stale
- **When** the sources block is collapsed
- **Then** the stale marker is not shown
- **And** after the user expands the block, the stale marker is shown next to that source

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
- **Then** the message displays the same sources in a collapsed block
