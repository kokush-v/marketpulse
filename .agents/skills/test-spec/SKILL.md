---
name: test-spec
description: Use when verifying an implemented OpenSpec change. Compares implementation against the spec, checks tasks, runs relevant tests, and reports gaps. Does not expand scope.
---

# Goal

Verify that an implemented OpenSpec change matches its approved specification and task list.

This skill is for testing, review, and gap detection. It may make small test fixes if explicitly asked, but it should not add new feature scope.

# Required Reading

Read:

- `openspec/project.md`
- `openspec/config.yaml`
- `AGENTS.md`
- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- `openspec/changes/<change-id>/specs/**/spec.md`
- Git diff for the current branch
- relevant changed source files
- relevant tests

# Workflow

1. Validate the OpenSpec change:

```bash
openspec validate <change-id> --strict
```

2. Compare implementation against:
   - proposal scope
   - spec requirements
   - Given/When/Then scenarios
   - tasks.md checklist
   - design.md constraints, if present

3. Check whether tests cover the changed behavior.
4. Run relevant checks where available.
5. Report gaps clearly.
6. Do not expand the feature scope.

# What To Check

## OpenSpec Alignment

- All ADDED/MODIFIED requirements are implemented.
- No out-of-scope behavior was added.
- Non-goals were respected.
- Tasks marked complete are actually implemented.
- Design constraints were followed.

## Backend Checks

- Protected endpoints validate Supabase access tokens where required.
- User-owned resources are scoped by authenticated user.
- Ownership is enforced in database queries.
- Async handlers do not call blocking SDK methods.
- SQLAlchemy `AsyncSession` is used consistently.
- Provider integrations handle failures, timeouts, rate limits, and malformed responses.
- Database model changes have Alembic migrations.
- Response schemas are explicit and OpenAPI-friendly.

## Frontend Checks

- Generated Orval clients are used where practical.
- API types are not duplicated manually.
- Async screens have loading, empty, and error states.
- Forms use React Hook Form and Zod where applicable.
- UI behavior matches the spec scenarios.

## Integration Checks

- Telegram integration uses async aiogram patterns.
- Notifications are idempotent where practical.
- External provider secrets are not exposed to frontend code.
- OpenAPI/Orval regeneration is included when API contracts changed.

# Suggested Commands

Use existing project scripts if they differ.

OpenSpec:

```bash
openspec validate <change-id> --strict
```

Backend:

```bash
cd backend
make lint
make test-unit
```

Frontend:

```bash
npm run lint
npm run typecheck
npm run test
```

# Report Format

Return:

## Result

Pass / Fail / Partial.

## Checked

- OpenSpec validation
- Backend checks
- Frontend checks
- Tests
- API contract / Orval checks

## Gaps

- Gap 1
- Gap 2

## Required Fixes

- Fix 1
- Fix 2

## Notes

Anything important for reviewers.

# Constraints

- Do not add new requirements.
- Do not expand scope.
- Do not perform large refactoring.
- Do not claim checks passed unless they were actually run.
- If checks cannot be run, state why.

# Next Step

After the implementation passes validation or the remaining gaps are resolved, the next skill in the default delivery flow is `create-pr`.

Use `create-pr` to prepare a focused pull request linked to the OpenSpec change and Linear issue, with a truthful summary of checks, risks, and reviewer notes.
