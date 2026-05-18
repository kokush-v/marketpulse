---
name: create-linear-task
description: Use when creating a Linear issue from an OpenSpec change. Creates a clear Linear task with scope, acceptance criteria, technical notes, validation steps, and links to the relevant OpenSpec change. Does not implement code.
---

# Goal

Create a Linear issue that accurately represents an OpenSpec change or a specific implementation task.

The OpenSpec change is the source of truth.

# Required Reading

Use the relevant OpenSpec files:

- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- `openspec/changes/<change-id>/specs/**/spec.md`

Also read:

- `openspec/project.md`
- `AGENTS.md`

# Rules

- Do not invent requirements.
- Do not expand scope beyond the OpenSpec change.
- Keep the Linear issue focused on one logical unit of work.
- If the OpenSpec change is too large, recommend splitting it into multiple Linear issues.
- Use the OpenSpec change ID in the Linear title or description.
- Include affected OpenSpec domains.
- Include acceptance criteria based on spec requirements and scenarios.
- Include implementation notes only when they are present in `design.md` or `tasks.md`.
- Include test expectations.
- Do not create implementation code.

# When To Split

Recommend splitting into multiple Linear issues when the change includes several independent units, for example:

- backend auth foundation
- frontend auth UI
- database migration
- Telegram integration
- background job processing
- API client generation

# Linear Issue Title

Prefer:

```text
<change-id>: <short action summary>
```

Examples:

```text
add-auth-foundation: define backend auth foundation
add-watchlist-management: implement user watchlists
add-orval-client-generation: generate frontend API client
```

# Linear Issue Body Format

Use this structure:

## Summary

Short description of the work.

## Background

Why this change is needed.

## Scope

- In-scope item 1
- In-scope item 2

## Non-Goals

- Out-of-scope item 1
- Out-of-scope item 2

## Acceptance Criteria

- [ ] Criterion based on OpenSpec requirement/scenario
- [ ] Criterion based on OpenSpec requirement/scenario

## Technical Notes

- Relevant backend/frontend/database/integration notes
- Mention migrations if required
- Mention Orval regeneration if API contracts change
- Mention async/provider concerns if relevant

## Validation

- [ ] `openspec validate <change-id> --strict`
- [ ] Relevant backend tests pass
- [ ] Relevant frontend checks pass
- [ ] API client regenerated if required

## Links

- OpenSpec change: `openspec/changes/<change-id>/`

# Output

If Linear tools are available:

- Create the Linear issue.
- Return the issue identifier and link.

If Linear tools are not available:

- Output the issue title and body in Markdown.
- State that the body should be pasted into Linear manually.

# Next Step

After the Linear issue is created from a valid OpenSpec change, the next skill in the default delivery flow is `implement-spec`.

Use `implement-spec` to validate the same change again, follow `tasks.md` in order, implement only approved scope, and update tests together with the code.
