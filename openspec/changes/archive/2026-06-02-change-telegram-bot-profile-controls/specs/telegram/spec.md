## MODIFIED Requirements

### Requirement: Support Explicit Telegram Account Switching
The system SHALL support a `Change account` bot flow that allows a Telegram account to move from one MarketPulse user to another only after explicit confirmation and a fresh web-issued linking token for the target account.

#### Scenario: User confirms account switch
- **Given** a Telegram account is actively linked to one MarketPulse user
- **And** the person using that Telegram account chooses `Change account`
- **And** a fresh valid linking token exists for a different authenticated MarketPulse user
- **When** the user explicitly confirms the switch in the bot
- **Then** the system deactivates the previous active Telegram link
- **And** the system activates the new Telegram link for the target authenticated user

#### Scenario: User does not confirm account switch
- **Given** a Telegram account is actively linked to one MarketPulse user
- **When** the person using that Telegram account starts `Change account` but does not confirm the switch
- **Then** the existing Telegram link remains unchanged

### Requirement: Allow Web Disconnect Of Telegram
The system SHALL allow an authenticated user to disconnect the currently linked Telegram account from the integrations workspace and SHALL allow the currently linked Telegram user to disconnect from the bot through an explicit confirmation flow.

#### Scenario: User disconnects Telegram from the web
- **Given** an authenticated user with an active Telegram link
- **When** the user disconnects Telegram from the integrations card
- **Then** the system deactivates that Telegram link for the current user
- **And** future Telegram notifications stop unless the user links Telegram again

#### Scenario: Linked user disconnects Telegram from the bot
- **Given** a Telegram account is actively linked to a MarketPulse user
- **When** the person using that Telegram account chooses `Unlink Profile` in the bot and confirms the action
- **Then** the system deactivates that Telegram link
- **And** future Telegram notifications stop unless the user links Telegram again

#### Scenario: Bot unlink is cancelled
- **Given** a Telegram account is actively linked to a MarketPulse user
- **When** the person using that Telegram account chooses `Unlink Profile` in the bot but does not confirm the action
- **Then** the existing Telegram link remains unchanged

#### Scenario: User disconnects without an active link
- **Given** an authenticated user without an active Telegram link
- **When** the user requests Telegram disconnect from the web or bot
- **Then** the system returns a safe no-op or equivalent frontend-safe outcome

## ADDED Requirements

### Requirement: Show Linked MarketPulse Profile In The Telegram Bot
The system SHALL allow a Telegram account with an active MarketPulse link to open a bot-side `Profile` view that shows the linked MarketPulse profile details.

#### Scenario: Linked user opens the bot profile
- **Given** a Telegram account is actively linked to a MarketPulse user
- **When** the person using that Telegram account opens `Profile` in the bot
- **Then** the system shows the linked MarketPulse profile avatar when one is available
- **And** the system shows the linked MarketPulse email
- **And** the system shows the linked MarketPulse display name

#### Scenario: Linked profile view exposes unlink action
- **Given** a Telegram account is actively linked to a MarketPulse user
- **When** the bot shows the `Profile` view
- **Then** the profile message includes an `Unlink Profile` reply-button action beneath the message

#### Scenario: Unlinked Telegram user opens the bot profile
- **Given** a Telegram account does not have an active MarketPulse link
- **When** the person using that Telegram account opens `Profile` in the bot
- **Then** the system returns a safe not-linked outcome
- **And** the system does not expose another user's profile details
