## MODIFIED Requirements

### Requirement: Propose Alert Mutations Through The Assistant

The system SHALL let an authenticated user ask the assistant to create, update, pause, resume, or delete an owned alert. The system SHALL present a clear summary of the target and relevant configuration and require explicit in-chat confirmation before performing the operation. The assistant SHALL treat a threshold stated in US dollars as a fixed USD price and a threshold stated in percent as a percentage change, and SHALL ask which one the user means when the threshold has no unit. The assistant SHALL treat an alert as one-time when the user does not ask for repetition and SHALL NOT ask about timing in that case. The assistant SHALL identify an existing alert from the user's own alerts using the coin the user names, optionally with its condition, and SHALL NOT ask the user to describe an alert that can be identified this way or mention alerts that do not exist.

#### Scenario: User proposes an alert creation or update

- **Given** an authenticated user requests a supported alert creation or update with complete valid configuration
- **When** the assistant validates the request
- **Then** it presents the alert rule, asset, timing, and requested change in a readable summary
- **And** no alert mutation occurs before confirmation

#### Scenario: User omits required alert data

- **Given** an authenticated user requests an alert creation or update without all required fields
- **When** the assistant evaluates the request
- **Then** it asks only for the missing or ambiguous information
- **And** creates no pending proposal or mutation

#### Scenario: User confirms an alert mutation

- **Given** an authenticated user has a current pending alert proposal in a conversation
- **When** the user explicitly confirms that proposal
- **Then** the system executes only that user's proposed alert mutation
- **And** reports the outcome in a new assistant message

#### Scenario: User states a threshold in US dollars

- **Given** an authenticated user asks for an alert when Bitcoin rises above 110000 USD
- **When** the assistant handles the request
- **Then** it presents a proposal for a fixed USD price threshold of 110000
- **And** it does not ask whether the threshold is a price or a percentage

#### Scenario: User states a threshold without a unit

- **Given** an authenticated user asks for an alert when Bitcoin goes above 110000 without a unit
- **When** the assistant handles the request
- **Then** it asks whether the threshold is a USD price or a percentage change
- **And** creates no pending proposal

#### Scenario: User does not mention alert timing

- **Given** an authenticated user asks for an alert about any new Solana news without mentioning timing
- **When** the assistant handles the request
- **Then** it presents a proposal for a one-time news alert
- **And** it does not ask whether the alert should repeat

#### Scenario: User names the coin of their only alert for that coin

- **Given** an authenticated user has exactly one alert for Bitcoin
- **When** the user asks the assistant to pause their Bitcoin alert
- **Then** the assistant presents a pause proposal for that alert
- **And** it does not ask the user to describe the alert

#### Scenario: User has several alerts for the named coin

- **Given** an authenticated user has two alerts for Solana
- **When** the user asks the assistant to pause their Solana alert
- **Then** the assistant lists those two alerts with their conditions and asks which one to pause
- **And** creates no pending proposal

#### Scenario: User names a coin without alerts

- **Given** an authenticated user has no alert for Dogecoin
- **When** the user asks the assistant to delete their Dogecoin alert
- **Then** the assistant states that no matching alert exists
- **And** it does not describe alerts that the user does not have
