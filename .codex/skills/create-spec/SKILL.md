---
name: create-spec
description: Use when creating or updating an OpenSpec change. Creates proposal.md, tasks.md, optional design.md, and spec delta files. Never implements application code.
---

# Goal

Create a clear, focused, valid OpenSpec change.

This skill is for spec creation only. It must not implement backend, frontend, database, or infrastructure code.

# Required Reading

Before creating or updating a change, read:

- `openspec/project.md`
- `openspec/config.yaml`
- `AGENTS.md`
- relevant current specs in `openspec/specs/`
- relevant active changes in `openspec/changes/`

# Clarification Rules

If the user request is short, vague, or missing important scope details, do not create the OpenSpec change immediately.

First ask focused clarification questions.

Ask only questions that affect scope, behavior, architecture, security, data model, or testing.

Do not ask unnecessary questions about implementation details that can be decided later in `design.md`.

Prefer 3 to 7 questions.

Group questions by topic when useful:

- Product scope
- User flows
- Backend behavior
- Frontend behavior
- Data model
- Security / ownership
- External integrations
- Testing

After the user answers, summarize the agreed scope and then create the OpenSpec change.

If the user explicitly says to make reasonable assumptions, document those assumptions in `proposal.md` and continue.

# Workflow

1. Understand the requested product or technical change.
2. Identify the affected OpenSpec domain:
   - `auth`
   - `watchlists`
   - `market-data`
   - `news`
   - `alerts`
   - `telegram`
   - `notifications`
   - `background-jobs`
   - `api-client-generation`
3. Choose a unique verb-led change ID, for example:
   - `add-watchlist-management`
   - `add-telegram-linking`
   - `change-alert-rule-cooldowns`
   - `fix-watchlist-symbol-duplicates`
4. Create or update:

```text
openspec/changes/<change-id>/
  proposal.md
  tasks.md
  design.md        # only when needed
  specs/
    <domain>/
      spec.md
```

5. Use `design.md` when the change includes:
   - database schema changes
   - authentication changes
   - background jobs
   - external API integrations
   - architectural decisions
   - API contract changes affecting Orval-generated frontend clients

6. Validate the change:

```bash
openspec validate <change-id> --strict
```

7. Fix validation errors.
8. Stop after the OpenSpec change is valid.

# Proposal Rules

`proposal.md` must include:

- Summary
- Problem
- Proposed Solution
- Scope
- Non-Goals
- Impact

Rules:

- Keep the proposal focused on one logical change.
- Include non-goals when scope could expand.
- Name affected domains and primary user workflows.
- Do not include low-level implementation details unless they affect scope or risk.
- Do not include implementation code.

# Spec Rules

Spec delta files must:

- Use `## ADDED Requirements`, `## MODIFIED Requirements`, or `## REMOVED Requirements`.
- Use RFC-style language:
   - `SHALL`
   - `SHOULD`
   - `MAY`
- Include at least one `#### Scenario:` per requirement.
- Use Given / When / Then format.
- Describe observable behavior, not implementation internals.
- Keep behavior user-scoped unless explicitly stated otherwise.

# Task Rules

`tasks.md` must:

- Break work into independently verifiable steps.
- Include backend tasks when backend behavior changes.
- Include frontend tasks when UI behavior changes.
- Include database/migration tasks when schema changes.
- Include integration tasks when external APIs are involved.
- Include tests.
- Include OpenAPI/Orval regeneration tasks when API contracts change.
- Include validation commands where relevant.

# Constraints

- Do not implement application code.
- Do not create migrations.
- Do not modify frontend or backend source files.
- Do not invent requirements.
- Do not expand scope beyond the user request.
- Do not create large multi-domain changes unless explicitly required.
- If requirements are unclear, ask for clarification.
