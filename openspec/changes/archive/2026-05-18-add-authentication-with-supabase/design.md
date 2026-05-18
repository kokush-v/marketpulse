## Overview
This change introduces end-to-end authentication behavior based on Supabase Auth for MarketPulse MVP. The architecture keeps Supabase as the identity provider while MarketPulse backend remains the trusted boundary for protected business data.

## Architectural Decisions

### 1. Identity Provider and Session Source
- Supabase Auth is the identity provider for user authentication.
- Frontend uses Supabase auth flows to establish session state.
- Backend validates Supabase access tokens for protected API calls.

### 2. Authorization Boundary
- Functional backend routes are protected and require a valid bearer token.
- Backend derives the acting user from validated JWT claims plus local `users` mapping.
- Ownership checks are enforced in backend data access, not only in frontend navigation.

### 3. Frontend Access Model
- Auth pages remain accessible to unauthenticated users.
- Product routes (dashboard and all functional application routes) are protected via route guards.
- Unauthenticated access attempts are redirected to sign-in.

### 4. Supported Auth Flows
- Email/password sign-up and sign-in.
- Google OAuth sign-in initiated on the frontend through the Supabase browser client.
- Sign-out.
- Password reset flow (request + completion).
- Email verification handling for sign-up lifecycle.

### 5. Google OAuth Ownership of Responsibilities
- Frontend is responsible for starting Google OAuth with Supabase and completing the callback in the same browser session.
- Frontend callback handling exchanges the returned auth code for a Supabase session using PKCE-compatible browser flow support.
- Backend does not act as the Google OAuth redirect target for the user-facing flow.
- Backend exposes an authenticated sync endpoint that provisions or refreshes the local `users` record after the frontend has obtained a valid Supabase access token.

## Security and Failure Handling
- Missing, malformed, expired, or invalid tokens result in unauthorized response for protected backend endpoints.
- Frontend handles unauthorized responses by clearing stale session assumptions and routing user back to sign-in.
- No role model is introduced; access is binary (authenticated vs unauthenticated) for MVP.
- The backend sync endpoint derives identity only from the validated Supabase JWT and does not trust user identity fields supplied by the frontend body.

## Data and Ownership Notes
- The local `users` representation remains the application mapping layer tied to Supabase identity.
- User-owned resource access is always scoped by authenticated user identity from token context.
- Client-supplied ownership identifiers are not trusted where user identity can be derived server-side.
- Local user synchronization after OAuth may create a new local user record or update the known email for an existing mapping.

## API and Client Contract Notes
- Auth API adds a backend synchronization endpoint for frontend-obtained Supabase sessions.
- If implementation introduces or modifies auth-related backend endpoints/schemas, OpenAPI schema updates must be reflected and Orval clients regenerated in the same implementation change.

## Risks and Rollback Considerations
- Risk: inconsistent guard behavior between frontend navigation and backend authorization can cause confusing UX.
- Mitigation: define explicit unauthorized behavior and test both UI guarding and API 401 handling.
- Rollback: auth UI and route guards can be reverted independently from backend token validation only if explicitly coordinated; otherwise keep changes unified to avoid security gaps.
