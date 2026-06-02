## Context

MarketPulse already has a protected `GET /auth/me` endpoint and an Orval-generated frontend client for it, but at least one authenticated UI surface still reads the user directly from Supabase in the browser. This change narrows the frontend contract so product UI consumes a backend-shaped current-user profile instead of the raw provider user object.

## Goals

- Make `GET /auth/me` the frontend-facing source of authenticated profile data for product UI.
- Keep the local `users` record as the primary source for application identity.
- Allow a small set of optional display fields to be enriched from Supabase for the same authenticated user.
- Preserve current unauthorized behavior and Orval-driven client generation.

## Non-Goals

- Changing Supabase session establishment or token storage flows.
- Changing account lifecycle routes such as sign-in, sign-up, or password reset.
- Adding profile editing.
- Expanding the response to arbitrary Supabase metadata fields.

## Response Contract Shape

`GET /auth/me` remains a protected endpoint. The response should be shaped for frontend consumption rather than mirroring either the local database row alone or the full Supabase user object.

The contract should include the currently used authenticated UI fields sourced from the local user record:

- `id`
- `email`

The contract may continue to include stable backend-owned identity metadata already exposed by the endpoint when needed by the application contract:

- `supabase_user_id`
- `created_at`

The contract should allow a narrow set of optional Supabase-enriched display fields for the same authenticated user:

- `display_name`
- `avatar_url`

Frontend-only derived presentation values, such as initials derived from the displayed name or email, should remain frontend concerns rather than backend contract fields.

## Data Sources

The backend resolves the authenticated local user from the validated access token exactly as it does for other protected endpoints.

Field ownership:

- local database: `id`, `supabase_user_id`, `email`, `created_at`
- Supabase enrichment: `display_name`, `avatar_url`

Supabase-enriched fields must be fetched only for the same authenticated Supabase user resolved from the validated token. The backend must not accept a client-supplied user identifier to choose which Supabase profile to read.

## Fallback Behavior

The local authenticated user record is required for a successful `GET /auth/me` response.

Optional Supabase-enriched fields are best-effort display data:

- if a selected Supabase profile field is missing, the endpoint should still return `200 OK` with the local user data
- if optional display enrichment cannot be obtained from Supabase, the endpoint should still return `200 OK` with the local user data and null optional fields

Missing, malformed, expired, or absent access tokens remain authorization failures and should continue to return `401 Unauthorized`.

## Frontend Contract Usage

The frontend should stop calling the browser Supabase user API for authenticated profile rendering that is covered by this change and should instead consume the generated client for `GET /auth/me`.

The existing sidebar-style UI can keep deriving compact presentation values such as initials from the returned profile fields. This avoids widening the API contract with formatting-specific values.

## API Client Generation

Because this change updates the `GET /auth/me` response contract, implementation must regenerate the Orval client artifacts and migrate the affected frontend consumer to the generated endpoint types and hooks.

## Risks And Rollback

Main risk:

- frontend and backend may temporarily disagree on the current-user payload shape if the contract changes without Orval regeneration and consumer updates

Rollback approach:

- revert the `GET /auth/me` contract change and the frontend consumer migration together if the integrated profile payload proves unstable
