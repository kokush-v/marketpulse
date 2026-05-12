---
name: marketpulse-create-openspec-change
description: Create a new OpenSpec change for MarketPulse by asking only missing requirement questions and generating the proper proposal, tasks, nested spec, and optional design files without implementing application code.
---

# MarketPulse OpenSpec Change Creator

Use this skill when the user wants to create a new OpenSpec change for MarketPulse.

## Goal

Help the user create a complete OpenSpec change folder without manually writing all files.

This skill must only create or update OpenSpec files. It must not implement application code.

## Project Context

MarketPulse is a web application for tracking stock prices, company news, watchlists, alerts, Telegram notifications, and daily digests.

Stack:

- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pytest, Ruff
- Frontend: Next.js 15+, TypeScript, App Router, TailwindCSS, shadcn/ui, TanStack Query, Zustand, React Hook Form, Zod, Axios, Recharts
- Infrastructure: AWS, Cognito, Docker, GitHub Actions, ECS, Secrets Manager, CloudWatch
- Integrations: Finnhub API, Telegram Bot API

## Required Questions

Before creating a change, ask only the missing questions from this list:

1. What feature or change should be added?
2. What problem does it solve?
3. What should be included in scope?
4. What should be out of scope?
5. Which parts are affected?
   - backend
   - frontend
   - bot
   - infra
   - background jobs
   - database
6. Are there any security, authentication, or user ownership rules?
7. What are the acceptance criteria?
8. Are tests required? If yes, which type?
   - unit
   - API
   - integration
   - E2E

Do not ask all questions if the answer is already clear from context.

## Linear MCP Rule

After creating and validating an OpenSpec change, suggest creating a Linear issue.

Do not create a Linear issue unless:

- `proposal.md` exists
- `tasks.md` exists
- nested `specs/<capability>/spec.md` exists
- `openspec validate <change-id> --strict` passes

## Output Files

Create this structure:

```text
openspec/changes/<kebab-case-change-name>/
  proposal.md
  tasks.md
  specs/<capability-name>/spec.md
  design.md
```

Do not create:

```text
openspec/changes/<change-name>/spec.md
```

The spec file must always be placed under:

```text
openspec/changes/<change-name>/specs/<capability-name>/spec.md
```

Use kebab-case for:

- change folder names
- capability folder names

Examples:

```text
openspec/changes/setup-project-foundation/specs/project-foundation/spec.md
openspec/changes/add-watchlists-crud/specs/watchlists/spec.md
openspec/changes/add-telegram-connection/specs/telegram/spec.md
```

Create `design.md` only when the change affects:

- architecture
- database models
- external integrations
- background jobs
- auth/security
- infrastructure

If none of these are affected, do not create `design.md`.

## proposal.md Format

```markdown
# Proposal: <Title>

## Problem

Explain the problem or missing capability.

## Scope

List what will be implemented.

## Out of Scope

List what will not be implemented.

## Acceptance Criteria

List concrete, testable acceptance criteria.

## Related Specs

List affected specs from openspec/specs.
```

## tasks.md Format

```markdown
# Tasks

## Backend

- [ ] ...

## Frontend

- [ ] ...

## Bot

- [ ] ...

## Database

- [ ] ...

## Background Jobs

- [ ] ...

## Infrastructure

- [ ] ...

## Tests

- [ ] ...
```

Only include relevant sections.

Do not include empty sections.

## Nested spec.md Format

The file must be created at:

```text
openspec/changes/<change-name>/specs/<capability-name>/spec.md
```

Use OpenSpec change markers.

For new capabilities, use:

```markdown
## ADDED Requirements

### Requirement: <Requirement name>

The system SHALL ...

#### Scenario: <Scenario name>

- Given ...
- When ...
- Then ...
```

For changes to existing capabilities, use:

```markdown
## MODIFIED Requirements

### Requirement: <Requirement name>

Updated requirement text.

#### Scenario: <Scenario name>

- Given ...
- When ...
- Then ...
```

For removed capabilities, use:

```markdown
## REMOVED Requirements

### Requirement: <Requirement name>

Reason for removal.
```

Rules for spec files:

- Use `SHALL` for normative requirements.
- Use concrete scenarios.
- Scenarios must be testable.
- Do not write vague requirements.
- Do not duplicate the same spec in the root change folder.
- Never create `openspec/changes/<change-name>/spec.md`.

## design.md Format

Include `design.md` only if needed.

```markdown
# Design: <Feature>

## Overview

Describe the technical approach.

## Data Model Changes

Describe database changes, if any.

## API Changes

Describe API routes, request/response contracts, and validation rules, if any.

## Background Job Changes

Describe scheduled jobs, retries, idempotency, and failure handling, if any.

## Integration Changes

Describe external provider or third-party integration changes, if any.

## Security Considerations

Describe authentication, authorization, user ownership, secret handling, and data exposure risks.

## Failure Handling

Describe expected failure cases and how the system should handle them.

## Open Questions

List unresolved questions that need user or team confirmation.
```

## Rules

- Do not implement application code.
- Only create or update OpenSpec files.
- Never create a root-level `spec.md` inside the change folder.
- Always create specs under `specs/<capability-name>/spec.md`.
- Always use OpenSpec markers:
   - `## ADDED Requirements`
   - `## MODIFIED Requirements`
   - `## REMOVED Requirements`

- Use kebab-case for change folder names.
- Use kebab-case for capability folder names.
- Keep acceptance criteria concrete and testable.
- Do not invent requirements that the user did not approve.
- If requirements are unclear, ask targeted questions first.
- If the user provides enough context, create the change without unnecessary questions.
- After creating files, return:
   - change folder path
   - files created
   - summary
   - open questions, if any
   - next recommended step
