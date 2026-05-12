# MarketPulse Repository Instructions

This repository follows OpenSpec-driven development.

## Current Repository State

- Product and architecture context lives in `openspec/project.md`.
- Proposed work lives under `openspec/changes/<change-id>/`.
- Existing behavior belongs under `openspec/specs/<capability>/spec.md` when specs exist.
- The current bootstrap change is `openspec/changes/setup-project-foundation/`.
- The `openspec/specs/` capability folders exist, but the repository may not have baseline `spec.md` files yet.
- Application code has not necessarily been created yet; check the workspace before assuming backend, frontend, Docker, or CI files exist.

## Global Rules

- OpenSpec is the source of truth.
- Do not implement application code without a valid OpenSpec change.
- Validate changes with `openspec validate <change-id> --strict`.
- Keep work scoped to the active OpenSpec change.
- Never create root-level `openspec/changes/<change-id>/spec.md`.
- Use nested specs: `openspec/changes/<change-id>/specs/<capability>/spec.md`.
- Do not expose secrets, tokens, provider API keys, or database credentials.
- User data must always be scoped by authenticated user.
- Read `openspec/project.md` before proposing, validating, or implementing MarketPulse work.
- Read relevant existing specs under `openspec/specs/` when they exist.

## Local Skill Usage

Use Codex skills for role-specific work:

- `marketpulse-create-openspec-change` to create a new MarketPulse OpenSpec change.
- `marketpulse-spec-agent` to create, validate, or refine OpenSpec changes.
- `marketpulse-implementation-agent` to implement an approved and valid MarketPulse OpenSpec change.
- `marketpulse-qa-agent` to verify tests, acceptance criteria, and edge cases after implementation.
- `marketpulse-review-agent` to review implementation changes against an OpenSpec change before commit, PR, or merge.
- `openspec-propose` to propose a new OpenSpec change with artifacts.
- `openspec-apply-change` to implement tasks from an approved OpenSpec change.
- `openspec-archive-change` to archive a completed OpenSpec change.
- `openspec-explore` to explore requirements or architecture before proposing a change.

## Implementation Guidance

- Before implementation, identify the active change and confirm its `proposal.md`, `tasks.md`, and nested specs are present and valid.
- For the foundation change, follow `openspec/changes/setup-project-foundation/` and avoid adding product features outside its scope.
- If implementation discoveries change expected behavior, update the relevant OpenSpec artifacts before or alongside code changes.
