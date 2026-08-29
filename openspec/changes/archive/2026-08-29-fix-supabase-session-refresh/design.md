## Context

Supabase Auth already establishes and persists the browser session, including its refresh token. MarketPulse additionally copies the access and refresh tokens to `mp_access_token` and `mp_refresh_token`. The shared API client reads the copied access token and treats the first `401 Unauthorized` response as an immediately invalid session, even when Supabase could refresh it.

## Session Ownership

The Supabase browser client is the only authority for browser authentication state and token persistence. MarketPulse code may request the current session and subscribe to Supabase auth events, but it does not maintain a second token store.

Existing `mp_access_token` and `mp_refresh_token` values are legacy duplicates. They are removed during frontend session initialization or explicit sign-out and are never used to authorize requests or reconstruct a missing Supabase session.

## Protected Request Flow

For a protected API request:

1. Obtain the current session from the Supabase browser client.
2. Attach its access token when a session exists.
3. Send the request.
4. If the response is not `401 Unauthorized`, handle it normally.
5. If the response is `401 Unauthorized`, request a Supabase session refresh.
6. If refresh returns a valid session, retry the original request exactly once with the new access token.
7. If refresh fails, returns no session, or the single retry is also unauthorized, clear the Supabase session and navigate to sign-in.

The retry is bounded so persistent authorization failures cannot create a loop.

## Concurrent Refresh

Multiple requests may receive `401 Unauthorized` at the same time when one access token expires. The frontend shares one in-flight refresh promise. Waiting requests reuse the resulting session and retry independently with the same refreshed access token. A failed shared refresh transitions the browser to the unauthenticated state once.

## Route Guard And Session Events

Protected route guards derive their initial state from the Supabase session rather than MarketPulse local-storage keys. They continue to subscribe to Supabase auth-state changes so sign-in, token refresh, and sign-out update protected-route access consistently.

## Recovery And Explicit Sign-Out

OAuth, email/password, and password-recovery flows continue to establish sessions through Supabase. Code that needs the access or refresh token for an existing backend operation obtains it from the current Supabase session at the time of the operation.

Explicit sign-out calls Supabase sign-out and removes any legacy MarketPulse token keys. Supabase remains responsible for deleting its own persisted session.

## Security And Failure Handling

- Refresh tokens remain managed by Supabase browser-session persistence.
- Tokens are not sent to any service other than Supabase and the existing MarketPulse backend authorization header flow.
- A transient or expired access token does not immediately destroy a refreshable session.
- A missing, revoked, or unrefreshable session still routes the user to sign-in.
- Retrying is limited to one attempt per original request.

## Rollout And Rollback

The change is frontend-only and requires no migration. Rollback restores the previous duplicated token utilities and immediate unauthorized handling. Legacy `mp_*` keys may be safely removed because they are copies, not the authoritative Supabase session.
