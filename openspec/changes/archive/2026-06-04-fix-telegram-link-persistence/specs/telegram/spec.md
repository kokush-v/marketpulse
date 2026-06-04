## MODIFIED Requirements

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
