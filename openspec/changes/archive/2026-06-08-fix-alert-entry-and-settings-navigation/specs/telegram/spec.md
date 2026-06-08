## MODIFIED Requirements

### Requirement: Provide A Protected Integrations Workspace For Telegram
The system SHALL provide authenticated users with a protected dashboard `Settings` workspace that exposes Telegram integration management for the current user only, and SHALL redirect legacy dashboard `Integrations` entry points into that settings workspace.

#### Scenario: Authenticated user opens settings
- **Given** an authenticated user
- **When** the user navigates to the dashboard `Settings` workspace
- **Then** the system shows the current Telegram integration state for that user only

#### Scenario: Authenticated user opens the legacy integrations route
- **Given** an authenticated user
- **When** the user requests the legacy dashboard `Integrations` route
- **Then** the system redirects the user to the dashboard `Settings` workspace
- **And** the Telegram integration management section remains available after the redirect

#### Scenario: Unauthenticated visitor requests settings
- **Given** a visitor without an authenticated session
- **When** the visitor requests the dashboard `Settings` workspace or the legacy dashboard `Integrations` route
- **Then** the system requires sign-in before granting access

### Requirement: Show Telegram Connection States In The Integrations Card
The system SHALL provide a Telegram integration card inside the dashboard `Settings` workspace that reflects whether the current user is not connected, has a fresh linking token ready, is connected, or encountered a safe integration error.

#### Scenario: User has no Telegram connection
- **Given** an authenticated user without an active Telegram link
- **When** the `Telegram` integration card renders in `Settings`
- **Then** the system shows a not-connected state and an affordance to start connection

#### Scenario: User starts connection
- **Given** an authenticated user without an active Telegram link
- **When** the user starts the Telegram connection flow
- **Then** the system shows a token-ready state with connect instructions

#### Scenario: User is already connected
- **Given** an authenticated user with an active Telegram link
- **When** the `Telegram` integration card renders in `Settings`
- **Then** the system shows a connected state for that user
