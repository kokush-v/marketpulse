# telegram Specification

## Purpose
TBD - created by archiving change add-telegram-notification-bot. Update Purpose after archive.
## Requirements
### Requirement: Provide A Protected Integrations Workspace For Telegram
The system SHALL provide authenticated users with a protected dashboard `Integrations` workspace that exposes Telegram integration management for the current user only.

#### Scenario: Authenticated user opens integrations
- **Given** an authenticated user
- **When** the user navigates to the dashboard `Integrations` workspace
- **Then** the system shows the current Telegram integration state for that user only

#### Scenario: Unauthenticated visitor requests integrations
- **Given** a visitor without an authenticated session
- **When** the visitor requests the dashboard `Integrations` workspace
- **Then** the system requires sign-in before granting access

### Requirement: Show Telegram Connection States In The Integrations Card
The system SHALL provide a Telegram integration card that reflects whether the current user is not connected, has a fresh linking token ready, is connected, or encountered a safe integration error.

#### Scenario: User has no Telegram connection
- **Given** an authenticated user without an active Telegram link
- **When** the `Telegram` integration card renders
- **Then** the system shows a not-connected state and an affordance to start connection

#### Scenario: User starts connection
- **Given** an authenticated user without an active Telegram link
- **When** the user starts the Telegram connection flow
- **Then** the system shows a token-ready state with connect instructions

#### Scenario: User is already connected
- **Given** an authenticated user with an active Telegram link
- **When** the `Telegram` integration card renders
- **Then** the system shows a connected state for that user

### Requirement: Connect Telegram Through Deep Link And Fallback Code
The system SHALL allow an authenticated user to initiate Telegram linking from the web app by generating a short-lived one-time token, exposing a bot deep link that includes that token, and exposing a copyable fallback code.

#### Scenario: User initiates Telegram linking
- **Given** an authenticated user without an active Telegram link
- **When** the user starts Telegram connection from the integrations card
- **Then** the system generates a short-lived one-time linking token for that user
- **And** the system shows an `Open bot` deep link that includes that token
- **And** the system shows a copyable fallback code for the same linking attempt

#### Scenario: User completes bot linking with valid token
- **Given** an authenticated user has started a Telegram connection flow
- **And** the user opens the bot using a valid current linking token
- **When** the bot receives and validates that token
- **Then** the system links the Telegram account to that authenticated user
- **And** the user's Telegram integration state becomes connected

#### Scenario: Successful bot linking remains available to subsequent bot actions
- **Given** an authenticated user has started a Telegram connection flow
- **And** the user completes bot linking with a valid current linking token
- **When** the same Telegram account opens a subsequent bot action such as `Profile`
- **Then** the system treats that Telegram account as actively linked
- **And** the system does not return a safe not-linked outcome caused only by the completed linking request failing to persist

#### Scenario: Linking token is expired or invalid
- **Given** an authenticated user attempts to complete Telegram linking
- **When** the provided linking token is expired, used, revoked, or invalid
- **Then** the system rejects the linking attempt with a safe error outcome
- **And** the user can start a new linking attempt from the web app

### Requirement: Enforce Single Active Ownership For Telegram Links
The system SHALL allow a Telegram account to be actively linked to at most one MarketPulse user at a time and SHALL allow each MarketPulse user to have at most one active Telegram link at a time.

#### Scenario: Telegram account is not linked elsewhere
- **Given** an authenticated user starts Telegram linking
- **And** the Telegram account is not actively linked to another user
- **When** the user completes the linking flow
- **Then** the system creates one active Telegram link for that user

#### Scenario: Telegram account is already linked elsewhere
- **Given** a Telegram account is actively linked to another MarketPulse user
- **When** a new linking flow attempts to use that Telegram account
- **Then** the system does not silently transfer the link
- **And** the system requires the explicit account-switch flow

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

