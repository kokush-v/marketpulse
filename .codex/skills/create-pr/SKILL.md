---
name: create-pr
description: Use when creating a pull request after an OpenSpec change has been implemented and tested. Creates a focused PR linked to the OpenSpec change and Linear issue. Does not expand scope.
---

# Goal

Create a pull request for a completed OpenSpec change.

The PR must be focused, reviewable, and linked to the OpenSpec change and Linear issue when available.

# Preconditions

Before creating a PR:

- The OpenSpec change must exist.
- Implementation tasks should be complete.
- Relevant tests and checks should be run where possible.
- The branch should contain only changes related to the selected OpenSpec change.

# Required Reading

Read:

- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- `openspec/changes/<change-id>/specs/**/spec.md`
- Git diff for the current branch
- Existing PR template if the repository has one:
   - `.github/pull_request_template.md`
   - `.github/PULL_REQUEST_TEMPLATE.md`

# Rules

- Do not create a PR for unrelated or mixed-scope changes.
- Do not claim tests passed unless they were actually run.
- If tests were not run, state that clearly.
- Link the Linear issue when available.
- Link or mention the OpenSpec change ID.
- Summarize user-visible behavior and important technical changes.
- Do not list every changed file unless needed for review.
- Include risks and rollback notes for non-trivial changes.
- Keep the PR title short and action-oriented.
- Do not modify implementation code unless explicitly asked.

# PR Title Format

Use one of:

```text
<change-id>: <short summary>
<linear-id>: <short summary>
<linear-id> <change-id>: <short summary>
```

Examples:

```text
add-auth-foundation: add backend auth foundation
MP-123: add backend auth foundation
MP-123 add-auth-foundation: add backend auth foundation
```

# PR Description Format

Use the repository PR template if one exists.

If no template exists, use:

## Summary

- What changed
- Why it changed

## OpenSpec

- Change: `openspec/changes/<change-id>/`
- Validation: `openspec validate <change-id> --strict`

## Linear

- Issue: `<linear-id or link>`

## Changes

- Backend:
   - ...
- Frontend:
   - ...
- Database:
   - ...
- Integrations:
   - ...

## Testing

- [ ] `openspec validate <change-id> --strict`
- [ ] Backend tests
- [ ] Frontend lint/typecheck/tests
- [ ] Orval regeneration checked if API contract changed

## Risks

- Risk 1
- Risk 2

## Notes for Reviewers

- Specific files or behavior that deserve attention

# Suggested Checks

Run relevant checks before creating the PR.

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

# Output

If GitHub tools are available:

- Create the PR.
- Return the PR link.

If GitHub tools are not available:

- Output the PR title and body in Markdown.
- State that the body should be pasted into GitHub manually.

# Constraints

- Do not expand scope.
- Do not hide failed or skipped checks.
- Do not create a PR with unrelated changes.
- Do not mark unchecked items as completed.
