## ADDED Requirements

### Requirement: Provide Frontend-Oriented Current User Profile

The system SHALL expose `GET /auth/me` as the frontend-facing authenticated profile endpoint for protected product UI.

#### Scenario: Authenticated product UI loads current profile from backend

- **Given** an authenticated user opens a protected product screen that needs current-user profile data
- **When** the frontend requests `GET /auth/me` with a valid Supabase access token
- **Then** the backend returns the authenticated user's current profile in a frontend-oriented response shape
- **And** the frontend can render the authenticated profile UI without directly reading the Supabase user object for that screen

### Requirement: Source Current User Profile From Local User And Selected Supabase Fields

The system SHALL return backend-owned authenticated identity fields from the local `users` record and MAY enrich the same response with selected display fields from Supabase for the same authenticated user.

#### Scenario: Local user data is returned for authenticated profile

- **Given** a valid `GET /auth/me` request for an authenticated user
- **When** the backend resolves the local MarketPulse user for the validated access token
- **Then** the response includes the local user identity fields required by the frontend contract
- **And** those local fields are sourced from the authenticated user's local `users` record

#### Scenario: Optional display fields are enriched from Supabase

- **Given** a valid `GET /auth/me` request for an authenticated user
- **When** selected display fields are available in Supabase for the same authenticated user
- **Then** the response includes those optional display fields as part of the current-user profile
- **And** the endpoint does not rely on a client-supplied user identifier to choose the Supabase profile

#### Scenario: Optional Supabase display fields are unavailable

- **Given** a valid `GET /auth/me` request for an authenticated user
- **And** the local MarketPulse user record exists
- **When** selected Supabase display fields are missing or temporarily unavailable
- **Then** the backend still returns `200 OK`
- **And** the response still includes the local authenticated user fields
- **And** optional display fields are omitted or null rather than causing the request to fail

### Requirement: Preserve Unauthorized Behavior For Current User Profile

The system SHALL continue to reject unauthorized `GET /auth/me` requests with `401 Unauthorized`.

#### Scenario: Access token is missing

- **Given** a request to `GET /auth/me`
- **When** no access token is provided
- **Then** the backend returns `401 Unauthorized`

#### Scenario: Access token is invalid or expired

- **Given** a request to `GET /auth/me`
- **When** the provided access token is invalid, malformed, or expired
- **Then** the backend returns `401 Unauthorized`
