---
name: implement-spec
description: Use when implementing an approved and valid OpenSpec change. Validates the change first, follows tasks.md exactly, updates code and tests, and avoids scope expansion.
---

# Goal

Implement an approved OpenSpec change with minimal, targeted code changes.

This skill is for implementation only. It must follow the approved OpenSpec change and must not invent or expand requirements.

# Preconditions

Before implementation:

- The OpenSpec change must exist.
- The change must be valid.
- The implementation scope must be clear.

Validate first:

```bash
openspec validate <change-id> --strict
```

Do not continue if validation fails. Fix the spec or ask for clarification.

# Required Reading

Read only the files needed for the selected change:

- `openspec/project.md`
- `openspec/config.yaml`
- `AGENTS.md`
- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/design.md` if it exists
- `openspec/changes/<change-id>/specs/**/spec.md`

Then inspect only directly relevant application files.

# Workflow

1. Validate the OpenSpec change.
2. Read the approved change files.
3. Summarize implementation assumptions to the user before writing code.
4. Use `ask_user` if any assumption could meaningfully affect scope or behavior.
5. Follow `tasks.md` in order.
6. Implement only the approved scope.
7. Add or update tests with the implementation.
8. Track progress in the SQL todos table when the task spans multiple steps.
9. Run relevant checks.
10. Validate OpenSpec again:

```bash
openspec validate <change-id> --strict
```

# Backend Implementation Rules

- Use feature-based FastAPI structure.
- Use async route handlers where I/O is involved.
- Use SQLAlchemy `AsyncSession`.
- Use `asyncpg` as the PostgreSQL async driver.
- Keep routes thin.
- Put business logic in `service.py`.
- Put non-trivial database queries in `repository.py`.
- Put Pydantic request and response schemas in `schemas.py`.
- Put SQLAlchemy models in `models.py`.
- Use `Annotated[Type, Depends(...)]` style for FastAPI dependency injection.
- Do not call blocking SDK methods inside async route handlers, services, Telegram handlers, or background jobs.
- Keep provider integrations behind service or provider interfaces.
- Enforce user ownership in queries, not only at the route layer.

# Frontend Implementation Rules

- Use Next.js App Router patterns.
- Use TypeScript.
- Use shadcn/ui for base components.
- Use TanStack Query for server state.
- Use React Hook Form and Zod for forms.
- Use Orval-generated API clients and hooks where practical.
- Do not manually duplicate generated API request or response types.
- Show loading, empty, and error states for async screens.

# API Contract Rules

When backend endpoint contracts change:

- Update explicit Pydantic request and response schemas.
- Ensure OpenAPI output remains stable and useful.
- Regenerate Orval clients when required.
- Update affected frontend usage in the same change.
- Update tests where needed.

# Testing Rules

- Add focused backend tests for changed behavior.
- Use `pytest-asyncio` for async behavior.
- Test authorization and ownership for user-owned resources.
- Test provider failure handling where relevant.
- Add frontend tests for important validation and UI states when practical.

# Constraints

- Do not add out-of-scope behavior.
- Do not rewrite specs unless explicitly asked.
- Do not perform broad refactoring unless required by the approved change.
- Do not read unrelated modules to infer hidden requirements.
- Do not mark tasks complete before code and tests are done.
- If implementation conflicts with the approved spec, stop and use `ask_user` for clarification.

# Next Step

After implementation and relevant checks are complete, the next skill in the default delivery flow is `test-spec`.
