## Summary
Add a complete authentication capability for MarketPulse using Supabase Auth, including email/password and Google sign-in, full account lifecycle flows, backend authorization enforcement, and frontend route guards for authenticated product access.

## Problem
MarketPulse currently has no formalized authentication behavior in OpenSpec. Without a defined auth capability, user access boundaries, protected routes, and account lifecycle flows are ambiguous, creating security and product consistency risks.

## Proposed Solution
Define an `auth` capability that standardizes:
- supported sign-in methods: email/password and Google OAuth
- user lifecycle flows: sign up, sign in, sign out, password reset, and email verification handling
- backend enforcement of Supabase JWT validation for protected API routes
- frontend-driven Google OAuth initiation and callback handling with backend user synchronization
- frontend route protection so product functionality is available only to authenticated users
- explicit unauthorized handling behavior for invalid or missing sessions

## Scope
In scope:
- Auth requirements for email/password and Google OAuth login
- Frontend callback handling for Google OAuth session establishment
- Backend synchronization of local user records after successful Google OAuth authentication
- Account lifecycle flows (registration, login, logout, password reset, email verification)
- Protected backend API behavior for functional endpoints
- Frontend auth pages and route guards for product screens
- Error and session-expiration behavior for unauthorized requests

## Non-Goals
- Role-based access control (RBAC) or admin/user roles
- Social providers beyond Google
- Telegram account linking changes
- Redesign of non-auth product features

## Impact
Affected domains:
- `auth`

Primary user workflows:
- New user account creation and verification
- Returning user sign-in via password or Google
- Returning user completion of Google OAuth callback and local account synchronization
- Password recovery
- Accessing protected product routes only while authenticated

System impact:
- Introduces cross-cutting auth and authorization behavior that backend and frontend implementations must follow.
- Requires OpenAPI/Orval alignment for any auth-related API contract updates during implementation.
