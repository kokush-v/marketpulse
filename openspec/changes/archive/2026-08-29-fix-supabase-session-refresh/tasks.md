## 1. Session Source Of Truth

- [x] 1.1 Replace MarketPulse-specific token persistence and reads with Supabase browser-session access.
- [x] 1.2 Remove legacy `mp_access_token` and `mp_refresh_token` values during session initialization and explicit sign-out.
- [x] 1.3 Update protected-route session evaluation and auth-dependent flows to read the current Supabase session.
- [x] 1.4 Extract shared Supabase session observation into a frontend hook and remove duplicated component-level subscriptions.

## 2. Protected API Recovery

- [x] 2.1 Resolve the current Supabase access token when preparing generated API requests.
- [x] 2.2 On `401 Unauthorized`, share one in-flight Supabase refresh across concurrent requests and retry each original request at most once.
- [x] 2.3 Transition to sign-in only when refresh fails, produces no valid session, or the retried request remains unauthorized.

## 3. Tests And Validation

- [x] 3.1 Update focused frontend auth tests for Supabase-backed route guarding and removal of duplicate token state.
- [x] 3.2 Add focused request-client tests for successful refresh-and-retry, failed refresh, repeated unauthorized responses, and concurrent refresh deduplication.
- [x] 3.3 Run frontend lint, type-check, and relevant test commands in Docker Compose.
- [x] 3.4 Run `openspec validate fix-supabase-session-refresh --strict`.
