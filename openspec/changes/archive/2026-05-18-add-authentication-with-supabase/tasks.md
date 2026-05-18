## 1. Backend auth foundation
- [x] 1.1 Add or update auth feature/module boundaries for Supabase JWT validation on protected routes.
- [x] 1.2 Implement authenticated-user dependency that resolves local user context from validated token.
- [x] 1.3 Enforce protected access on functional API routes and return unauthorized responses for invalid/missing tokens.

## 2. Backend auth flows
- [x] 2.1 Add or update backend contracts needed for auth lifecycle integration (including frontend-driven Google OAuth user sync).
- [x] 2.2 Ensure sign-out and session-invalid handling is consistent for protected API access.
- [x] 2.3 Ensure ownership is derived from authenticated context for user-owned resources.

## 3. Frontend auth pages and guards
- [x] 3.1 Add auth screens and flows for sign up, sign in, Google sign-in entry, frontend OAuth callback completion, password reset request, password reset completion, and sign out entrypoint.
- [x] 3.2 Add route guard behavior so functional product routes are accessible only to authenticated users.
- [x] 3.3 Ensure unauthenticated users are redirected to sign-in and authenticated users are redirected away from auth pages when appropriate.
- [x] 3.4 Add loading and error states for auth/session checks and auth form submissions.

## 4. API client and contract alignment
- [x] 4.1 Regenerate frontend API clients with Orval if backend auth-related OpenAPI contracts are added or changed.
- [x] 4.2 Update frontend usage to match generated types/hooks where contract changes apply.

## 5. Tests
- [x] 5.1 Add backend tests for protected route authorization outcomes (valid token, missing token, invalid/expired token).
- [x] 5.2 Add backend tests for ownership scoping via authenticated user context and frontend-driven OAuth user synchronization.

## 6. Validation
- [x] 6.1 Run `openspec validate add-authentication-with-supabase --strict` before implementation.
- [x] 6.2 Run relevant backend and frontend quality gates during implementation PR.
- [x] 6.3 Run `openspec validate add-authentication-with-supabase --strict` after implementation updates.
