# auth Specification

## Purpose
Define how MarketPulse authenticates users with Supabase Auth, protects product routes and backend APIs, synchronizes local user identity, and returns users to a valid unauthenticated state when sessions become invalid.
## Requirements
### Requirement: Support Email/Password and Google Authentication
The system SHALL support user authentication through both email/password credentials and Google OAuth.

#### Scenario: Email/password sign-in success
- **Given** a user with a valid email/password account
- **When** the user submits correct credentials
- **Then** the system authenticates the user and establishes an authenticated session

#### Scenario: Google sign-in success
- **Given** a user selects Google sign-in
- **When** the OAuth flow completes successfully
- **Then** the system authenticates the user and establishes an authenticated session

#### Scenario: Google sign-in completes through frontend callback and backend sync
- **Given** a user returns from Google OAuth to the frontend callback route
- **When** the frontend establishes a Supabase session and calls the backend with the resulting access token
- **Then** the backend validates the token and creates or updates the local authenticated user mapping from token identity

### Requirement: Provide Full Account Lifecycle Flows
The system SHALL provide account lifecycle flows for sign up, sign in, sign out, password reset, and email verification handling.

#### Scenario: New user registration
- **Given** a visitor without an account
- **When** the visitor completes sign-up with valid registration data
- **Then** the system creates an account and proceeds according to verification requirements

#### Scenario: Password reset request
- **Given** a user who cannot access their password
- **When** the user submits a password reset request for a registered email
- **Then** the system initiates the password reset flow

#### Scenario: Sign-out
- **Given** an authenticated user
- **When** the user signs out
- **Then** the session is terminated and protected product routes are no longer accessible until re-authentication

### Requirement: Protect Functional Product Routes
The system SHALL restrict all functional product routes to authenticated users only.

#### Scenario: Unauthenticated access to a protected product route
- **Given** a visitor without an authenticated session
- **When** the visitor requests a protected product route
- **Then** the system redirects the visitor to sign-in

#### Scenario: Authenticated access to a protected product route
- **Given** a user with an authenticated session
- **When** the user requests a protected product route
- **Then** the system grants access

### Requirement: Enforce Backend Authorization for Protected APIs
The backend SHALL validate Supabase access tokens on protected functional endpoints and derive user context from the validated token.

#### Scenario: Protected API call with valid token
- **Given** a request to a protected functional API endpoint
- **When** the request includes a valid Supabase access token
- **Then** the backend authorizes the request and resolves the current user context from token identity

#### Scenario: Protected API call with missing token
- **Given** a request to a protected functional API endpoint
- **When** no access token is provided
- **Then** the backend rejects the request as unauthorized

#### Scenario: Protected API call with invalid or expired token
- **Given** a request to a protected functional API endpoint
- **When** the access token is invalid, malformed, or expired
- **Then** the backend rejects the request as unauthorized

### Requirement: Enforce Ownership from Authenticated Context
The backend SHALL enforce user-owned resource access using authenticated user context rather than trusting client-supplied ownership identifiers.

#### Scenario: Client attempts cross-user access via identifier tampering
- **Given** an authenticated request for a user-owned resource
- **When** the request includes an ownership identifier that does not match the authenticated user
- **Then** the backend enforces ownership based on authenticated context and prevents cross-user access

### Requirement: Handle Unauthorized Session State in Frontend
The frontend SHALL handle unauthorized API outcomes by transitioning users to a valid unauthenticated state and requiring re-authentication for protected routes.

#### Scenario: Session becomes invalid during active product usage
- **Given** a user currently navigating protected product screens
- **When** protected API responses indicate unauthorized access
- **Then** the frontend treats the session as unauthenticated and routes the user to sign-in
