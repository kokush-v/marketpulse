## Summary

Make the Supabase browser session the frontend's single source of truth for authentication tokens and recover protected API requests through session refresh before signing the user out.

## Problem

The frontend currently duplicates Supabase access and refresh tokens into MarketPulse-specific local-storage keys. Protected API requests read the duplicated access token and immediately clear the session after any `401 Unauthorized` response. The duplicated token can be stale while Supabase still has a refreshable session, causing users to be signed out instead of transparently receiving a refreshed access token.

## Proposed Solution

Read authentication state and access tokens from the Supabase browser client only. Before protected requests, use the current Supabase session. When a protected request receives `401 Unauthorized`, refresh the Supabase session, retry the original request once with the refreshed access token, and transition to sign-in only when no valid refreshed session can be established. Concurrent unauthorized requests share one refresh attempt.

## Scope

Affected domain:

- `auth`

Primary workflows:

- preserve an authenticated session across access-token expiry
- attach the current Supabase access token to generated API requests
- refresh and retry once after an unauthorized protected request
- sign out when the Supabase session is genuinely invalid or cannot be refreshed
- remove MarketPulse-specific duplicate token persistence and reads

## Non-Goals

- changing Supabase project token lifetime or refresh-token rotation settings
- changing backend JWT validation or protected API contracts
- adding a backend refresh-token endpoint
- changing sign-in, sign-up, OAuth, recovery, or explicit sign-out product behavior
- storing authentication tokens in application state, cookies managed outside Supabase, or the MarketPulse database

## Impact

Frontend authentication utilities, route guards, password-recovery flows, explicit sign-out handling, and the shared Orval request client will use the Supabase browser session consistently. No database migration, backend change, or generated API contract change is required.
