## Summary

Refine the authenticated user profile contract so the frontend reads its current-user data from the backend `GET /auth/me` endpoint instead of directly reading the Supabase user object for UI profile rendering.

## Problem

The frontend currently reads the authenticated user directly from Supabase for product UI display. That exposes a larger provider-shaped payload than the UI needs and bypasses the backend as the trusted boundary for shaping authenticated product data.

MarketPulse already exposes `GET /auth/me`, but the current contract does not define the frontend-oriented profile payload needed for authenticated UI surfaces, nor does it define how backend-owned user data should be combined with selected Supabase profile fields.

## Proposed Solution

Change the `auth` domain contract so `GET /auth/me` becomes the frontend-facing source for the authenticated user profile used in product UI.

The endpoint will continue to authorize via the Supabase access token and resolve the local MarketPulse user from the database. It will return the local user identity fields needed by the frontend and may enrich the response with a narrow set of Supabase profile fields used for display.

The frontend will switch existing authenticated profile rendering from direct Supabase user reads to the generated client for `GET /auth/me`.

## Scope

Affected domains:

- `auth`
- `api-client-generation`

Primary user workflows:

- an authenticated user opens a protected product screen and the UI loads the current user profile from `GET /auth/me`
- authenticated profile UI renders from the backend response instead of a direct Supabase user read
- an expired or invalid session still results in `401 Unauthorized` and frontend sign-in recovery

In scope:

- defining the frontend-oriented response contract for `GET /auth/me`
- requiring backend-owned user data to come from the local `users` record
- allowing selected profile display fields to be enriched from Supabase for the same authenticated user
- switching existing frontend authenticated profile display to the backend endpoint
- regenerating Orval clients for the updated endpoint contract

## Non-Goals

- changing sign-in, sign-up, sign-out, password reset, or OAuth flows
- changing how Supabase sessions or tokens are established on the frontend
- migrating additional product screens beyond the authenticated user profile reads covered by this change
- adding new user-editing or profile-management capabilities
- changing the unauthorized handling flow beyond continuing to use `401 Unauthorized`

## Impact

This change makes the backend the trusted boundary for authenticated profile data used by the product UI, reduces frontend dependence on the raw Supabase user object, and keeps the generated API client aligned with the user profile contract the frontend actually consumes.
