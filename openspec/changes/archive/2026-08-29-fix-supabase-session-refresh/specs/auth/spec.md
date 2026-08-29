## MODIFIED Requirements

### Requirement: Handle Unauthorized Session State in Frontend

The frontend SHALL use the persisted Supabase browser session as the single source of truth for authentication tokens. When a protected API request is unauthorized, the frontend SHALL attempt to refresh the Supabase session and retry the original request once before treating the user as unauthenticated. The frontend SHALL NOT maintain separate application-owned access-token or refresh-token persistence.

#### Scenario: Expired access token is refreshed successfully

- **Given** a user has a refreshable Supabase browser session with an expired or rejected access token
- **When** a protected API request returns `401 Unauthorized`
- **Then** the frontend refreshes the Supabase session
- **And** retries the original request once with the refreshed access token
- **And** preserves the authenticated session when the retry succeeds

#### Scenario: Multiple requests become unauthorized concurrently

- **Given** multiple protected API requests use the same expired or rejected access token
- **When** those requests return `401 Unauthorized` concurrently
- **Then** the frontend performs one shared Supabase session refresh
- **And** each request retries at most once with the resulting access token

#### Scenario: Session cannot be refreshed

- **Given** a protected API request returns `401 Unauthorized`
- **When** Supabase cannot provide a valid refreshed session
- **Then** the frontend transitions the user to a valid unauthenticated state
- **And** routes the user to sign-in

#### Scenario: Retried request remains unauthorized

- **Given** Supabase returns a refreshed session after an unauthorized protected request
- **When** the single retry also returns `401 Unauthorized`
- **Then** the frontend does not retry again
- **And** transitions the user to sign-in

#### Scenario: Frontend resolves authentication state

- **Given** the frontend needs to authorize a request or protect a product route
- **When** it evaluates the current authentication state
- **Then** it reads the Supabase browser session
- **And** does not depend on a duplicate MarketPulse token store
