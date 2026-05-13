## 1. Backend auth foundation
- [ ] 1.1 Add or update auth feature/module boundaries for Supabase JWT validation on protected routes.
- [ ] 1.2 Implement authenticated-user dependency that resolves local user context from validated token.
- [ ] 1.3 Enforce protected access on functional API routes and return unauthorized responses for invalid/missing tokens.

## 2. Backend auth flows
- [ ] 2.1 Add or update backend contracts needed for auth lifecycle integration (if any backend endpoints are required by architecture).
- [ ] 2.2 Ensure sign-out and session-invalid handling is consistent for protected API access.
- [ ] 2.3 Ensure ownership is derived from authenticated context for user-owned resources.

## 3. Frontend auth pages and guards
- [ ] 3.1 Add auth screens and flows for sign up, sign in, Google sign-in entry, password reset request, password reset completion, and sign out entrypoint.
- [ ] 3.2 Add route guard behavior so functional product routes are accessible only to authenticated users.
- [ ] 3.3 Ensure unauthenticated users are redirected to sign-in and authenticated users are redirected away from auth pages when appropriate.
- [ ] 3.4 Add loading and error states for auth/session checks and auth form submissions.

## 4. API client and contract alignment
- [ ] 4.1 Regenerate frontend API clients with Orval if backend auth-related OpenAPI contracts are added or changed.
- [ ] 4.2 Update frontend usage to match generated types/hooks where contract changes apply.

## 5. Tests
- [ ] 5.1 Add backend tests for protected route authorization outcomes (valid token, missing token, invalid/expired token).
- [ ] 5.2 Add backend tests for ownership scoping via authenticated user context.
- [ ] 5.3 Add frontend tests for route guard behavior and major auth flows (sign in, sign up, password reset entry).
- [ ] 5.4 Add frontend tests for unauthorized response handling and redirect behavior.

## 6. Validation
- [ ] 6.1 Run `openspec validate add-authentication-with-supabase --strict` before implementation.
- [ ] 6.2 Run relevant backend and frontend quality gates during implementation PR.
- [ ] 6.3 Run `openspec validate add-authentication-with-supabase --strict` after implementation updates.
