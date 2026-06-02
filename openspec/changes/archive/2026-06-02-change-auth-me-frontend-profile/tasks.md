## 1. Spec Updates

- [x] 1.1 Update the `auth` domain contract to define `GET /auth/me` as the frontend-facing authenticated profile endpoint for product UI.
- [x] 1.2 Update the `auth` domain contract to define which fields come from the local MarketPulse user record and which display fields may be enriched from Supabase for the same authenticated user.
- [x] 1.3 Update the `auth` domain contract to preserve `401 Unauthorized` behavior for missing, invalid, or expired access tokens when calling `GET /auth/me`.

## 2. Design

- [x] 2.1 Document how `GET /auth/me` combines local user data with selected Supabase profile fields without changing authentication ownership rules.
- [x] 2.2 Document safe fallback behavior when optional Supabase profile data is unavailable while the local authenticated user record exists.
- [x] 2.3 Document the API contract implications for the generated frontend client.

## 3. Implementation

- [x] 3.1 Update the backend auth response schema and `GET /auth/me` implementation to return the approved frontend-oriented current-user payload.
- [x] 3.2 Update backend tests for `GET /auth/me` to cover the approved payload shape and optional Supabase profile enrichment behavior.
- [x] 3.3 Regenerate the frontend Orval client for the updated auth contract.
- [x] 3.4 Update the frontend authenticated user profile read to use the generated `GET /auth/me` client instead of direct Supabase user fetching.

## 4. Validation

- [x] 4.1 Run `openspec validate change-auth-me-frontend-profile --strict`.
- [x] 4.2 Run relevant backend and frontend quality checks for the auth profile contract change.
